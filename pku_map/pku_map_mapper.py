#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
北京大学校园地图节点标注与映射系统 (PKU Campus Map Node Mapping System)

功能说明:
1. 读取高清校园地图图片和CSV节点表格
2. 将CSV中的节点坐标映射到高清地图上，绘制标记点
3. 支持路径规划：给定节点序列，在地图上绘制路线
4. 支持交互式查询：按节点ID或名称查询位置
5. 所有坐标基于相对坐标系(0-1)，可自适应任意分辨率

映射规则 (Mapping Rules):
- 坐标系: 左上角为原点(0,0), 右下角为(1,1)
- x: 水平方向相对坐标 (0=left, 1=right)
- y: 垂直方向相对坐标 (0=top, 1=bottom)
- 标记格式: 红色圆圈+白色边框+编号+中英文名称
- 路径格式: 蓝色虚线连接节点，箭头指示方向
"""

import csv
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import numpy as np


class PKUMapMapper:
    """北京大学地图节点映射类"""
    
    # 类别颜色映射
    CATEGORY_COLORS = {
        'gate': '#FF4444',       # 校门 - 红色
        'landmark': '#FFD700',   # 地标 - 金色
        'building': '#4488FF',   # 建筑 - 蓝色
        'garden': '#44CC44',     # 园林 - 绿色
        'landscape': '#00CED1',  # 景观 - 青色
        'sports': '#FF8844',     # 体育 - 橙色
    }
    
    # 类别中文名称
    CATEGORY_NAMES = {
        'gate': '校门',
        'landmark': '地标',
        'building': '建筑',
        'garden': '园林',
        'landscape': '景观',
        'sports': '体育',
    }
    
    def __init__(self, map_path=None, nodes_csv_path=None):
        """
        初始化映射器
        
        Args:
            map_path: 高清地图图片路径，默认使用同级目录的 pku_campus_map_hd.png
            nodes_csv_path: 节点CSV文件路径，默认使用同级目录的 pku_nodes.csv
        """
        script_dir = Path(__file__).parent.absolute()
        
        self.map_path = map_path or str(script_dir / 'pku_campus_map_hd.png')
        self.nodes_csv_path = nodes_csv_path or str(script_dir / 'pku_nodes.csv')
        
        # 加载地图图片
        if not os.path.exists(self.map_path):
            raise FileNotFoundError(f"地图图片未找到: {self.map_path}")
        self.map_img = Image.open(self.map_path)
        self.map_width, self.map_height = self.map_img.size
        print(f"地图已加载: {self.map_width} x {self.map_height} 像素")
        
        # 加载节点数据
        if not os.path.exists(self.nodes_csv_path):
            raise FileNotFoundError(f"节点CSV未找到: {self.nodes_csv_path}")
        with open(self.nodes_csv_path, encoding="utf-8") as f:
            self.nodes_rows = list(csv.DictReader(f))
        print(f"节点已加载: {len(self.nodes_rows)} 个节点")

        # 构建节点ID到数据的映射
        self.node_dict = {}
        for row in self.nodes_rows:
            self.node_dict[int(row['node_id'])] = {
                'name': row['name'],
                'name_en': row['name_en'],
                'category': row['category'],
                'x': float(row['x']),
                'y': float(row['y']),
                'description': row['description']
            }
    
    def relative_to_pixel(self, x, y):
        """
        将相对坐标(0-1)转换为像素坐标
        
        Mapping Rule:
            pixel_x = relative_x * image_width
            pixel_y = relative_y * image_height
        
        Returns:
            (pixel_x, pixel_y)
        """
        pixel_x = int(x * self.map_width)
        pixel_y = int(y * self.map_height)
        return (pixel_x, pixel_y)
    
    def pixel_to_relative(self, px, py):
        """
        将像素坐标转换为相对坐标(0-1)
        
        Returns:
            (relative_x, relative_y)
        """
        rel_x = px / self.map_width
        rel_y = py / self.map_height
        return (rel_x, rel_y)
    
    def get_node_pixel_coords(self, node_id):
        """
        获取指定节点的像素坐标
        
        Args:
            node_id: 节点ID
            
        Returns:
            (pixel_x, pixel_y) 或 None
        """
        if node_id not in self.node_dict:
            return None
        node = self.node_dict[node_id]
        return self.relative_to_pixel(node['x'], node['y'])
    
    def annotate_map(self, output_path=None, show_labels=True, highlight_nodes=None):
        """
        在高清地图上标注所有节点
        
        Args:
            output_path: 输出图片路径，默认保存为 annotated_map.png
            show_labels: 是否显示节点标签
            highlight_nodes: 要高亮显示的节点ID列表(红色大圈)
            
        Returns:
            输出图片的绝对路径
        """
        output_path = output_path or str(Path(self.map_path).parent / 'annotated_map.png')
        highlight_nodes = highlight_nodes or []
        
        # 创建地图副本
        annotated = self.map_img.copy()
        draw = ImageDraw.Draw(annotated)
        
        # 尝试加载中文字体
        font = self._get_font(size=16)
        font_small = self._get_font(size=12)
        font_id = self._get_font(size=14)
        
        # 绘制每个节点
        for node_id, node in self.node_dict.items():
            px, py = self.relative_to_pixel(node['x'], node['y'])
            color = self.CATEGORY_COLORS.get(node['category'], '#888888')
            is_highlight = node_id in highlight_nodes
            
            radius = 18 if is_highlight else 12
            outline_width = 4 if is_highlight else 2
            
            # 绘制节点圆圈 (外圈白色，内圈类别色)
            # 外圈（白色边框）
            draw.ellipse(
                [px - radius - 2, py - radius - 2, px + radius + 2, py + radius + 2],
                fill='white',
                outline='white'
            )
            # 内圈（类别颜色）
            draw.ellipse(
                [px - radius, py - radius, px + radius, py + radius],
                fill=color,
                outline='white'
            )
            
            # 绘制节点ID
            id_text = str(node_id)
            bbox = draw.textbbox((0, 0), id_text, font=font_id)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((px - tw//2, py - th//2 - 1), id_text, fill='white', font=font_id)
            
            if show_labels:
                # 绘制节点名称（中文）
                name_text = node['name']
                bbox = draw.textbbox((0, 0), name_text, font=font_small)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                
                # 标签背景
                label_x = px - tw // 2
                label_y = py + radius + 4
                draw.rectangle(
                    [label_x - 3, label_y - 1, label_x + tw + 3, label_y + th + 1],
                    fill=(255, 255, 255, 200),
                    outline=(0, 0, 0, 100)
                )
                # 标签文字
                draw.text((label_x, label_y), name_text, fill='black', font=font_small)
        
        # 绘制图例
        self._draw_legend(draw, font_small)
        
        annotated.save(output_path, 'PNG', quality=95)
        print(f"标注地图已保存: {output_path}")
        return os.path.abspath(output_path)
    
    def draw_path(self, node_ids, output_path=None, path_color='#FF0066', 
                  path_width=5, show_direction=True):
        """
        在地图上绘制节点路径
        
        Args:
            node_ids: 节点ID列表，按路径顺序
            output_path: 输出图片路径
            path_color: 路径颜色
            path_width: 路径线宽
            show_direction: 是否显示方向箭头
            
        Returns:
            输出图片的绝对路径
        """
        output_path = output_path or str(Path(self.map_path).parent / 'path_map.png')
        
        # 先复制原图并标注所有节点
        annotated = self.map_img.copy()
        draw = ImageDraw.Draw(annotated)
        
        font = self._get_font(size=14)
        font_small = self._get_font(size=11)
        
        # 绘制所有节点（小标记，半透明）
        for node_id, node in self.node_dict.items():
            px, py = self.relative_to_pixel(node['x'], node['y'])
            color = self.CATEGORY_COLORS.get(node['category'], '#888888')
            draw.ellipse(
                [px - 8, py - 8, px + 8, py + 8],
                fill=color + '88',  # 半透明
                outline='white'
            )
        
        # 收集路径上的坐标
        path_coords = []
        for nid in node_ids:
            if nid in self.node_dict:
                px, py = self.get_node_pixel_coords(nid)
                path_coords.append((px, py, nid))
        
        if len(path_coords) < 2:
            print("路径至少需要2个节点")
            return None
        
        # 绘制路径线段
        for i in range(len(path_coords) - 1):
            x1, y1, _ = path_coords[i]
            x2, y2, _ = path_coords[i + 1]
            
            # 绘制粗线（阴影效果）
            draw.line([(x1, y1), (x2, y2)], fill='#00000066', width=path_width + 4)
            # 绘制主线
            draw.line([(x1, y1), (x2, y2)], fill=path_color, width=path_width)
            
            # 绘制方向箭头
            if show_direction:
                self._draw_arrow(draw, x1, y1, x2, y2, path_color)
        
        # 高亮路径节点
        for i, (px, py, nid) in enumerate(path_coords):
            node = self.node_dict[nid]
            
            # 大圆圈高亮
            radius = 20
            draw.ellipse(
                [px - radius, py - radius, px + radius, py + radius],
                fill=path_color,
                outline='white'
            )
            # 白色内圈
            draw.ellipse(
                [px - radius + 5, py - radius + 5, px + radius - 5, py + radius - 5],
                fill='white',
                outline=path_color
            )
            
            # 节点ID和序号
            order_text = str(i + 1)
            bbox = draw.textbbox((0, 0), order_text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text((px - tw//2, py - th//2 - 1), order_text, fill=path_color, font=font)
            
            # 节点名称
            name_text = f"{nid}:{node['name']}"
            bbox = draw.textbbox((0, 0), name_text, font=font_small)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            
            label_x = px + radius + 5
            label_y = py - th // 2
            
            # 避免标签超出边界
            if label_x + tw > self.map_width - 20:
                label_x = px - radius - tw - 5
            if label_y < 10:
                label_y = py + radius + 5
                
            draw.rectangle(
                [label_x - 2, label_y - 1, label_x + tw + 2, label_y + th + 1],
                fill='white'
            )
            draw.text((label_x, label_y), name_text, fill='black', font=font_small)
        
        annotated.save(output_path, 'PNG', quality=95)
        print(f"路径地图已保存: {output_path}")
        return os.path.abspath(output_path)
    
    def query_node(self, query):
        """
        查询节点信息
        
        Args:
            query: 节点ID(int)或名称(str)
            
        Returns:
            节点信息字典或None
        """
        if isinstance(query, int) or (isinstance(query, str) and query.isdigit()):
            node_id = int(query)
            if node_id in self.node_dict:
                info = self.node_dict[node_id].copy()
                info['node_id'] = node_id
                info['pixel_coords'] = self.get_node_pixel_coords(node_id)
                return info
        
        # 按名称模糊匹配
        query_str = str(query)
        for node_id, node in self.node_dict.items():
            if query_str in node['name'] or query_str.lower() in node['name_en'].lower():
                info = node.copy()
                info['node_id'] = node_id
                info['pixel_coords'] = self.get_node_pixel_coords(node_id)
                return info
        
        return None
    
    def list_nodes_by_category(self, category):
        """
        按类别列出所有节点
        
        Args:
            category: 类别名称(gate/landmark/building/garden/landscape/sports)
            
        Returns:
            节点列表
        """
        results = []
        for node_id, node in self.node_dict.items():
            if node['category'] == category:
                info = node.copy()
                info['node_id'] = node_id
                results.append(info)
        return results
    
    def get_mapping_summary(self):
        """
        获取映射摘要信息
        
        Returns:
            摘要字符串
        """
        lines = []
        lines.append("=" * 60)
        lines.append("北京大学校园地图节点映射摘要")
        lines.append("=" * 60)
        lines.append(f"地图尺寸: {self.map_width} x {self.map_height} 像素")
        lines.append(f"节点总数: {len(self.nodes_rows)}")
        lines.append("")
        lines.append("节点类别分布:")
        categories = {}
        for row in self.nodes_rows:
            cat = row['category']
            categories[cat] = categories.get(cat, 0) + 1
        for cat, count in categories.items():
            cn_name = self.CATEGORY_NAMES.get(cat, cat)
            lines.append(f"  {cn_name}({cat}): {count}个")
        lines.append("")
        lines.append("坐标系说明:")
        lines.append("  - 相对坐标范围: x[0.0, 1.0], y[0.0, 1.0]")
        lines.append("  - 原点(0,0): 左上角")
        lines.append("  - 像素转换: px = rel_x * width, py = rel_y * height")
        lines.append("")
        lines.append("示例节点坐标:")
        for nid in [9, 8, 10, 1, 5]:
            if nid in self.node_dict:
                node = self.node_dict[nid]
                px, py = self.get_node_pixel_coords(nid)
                lines.append(f"  节点{nid} {node['name']}: 相对({node['x']:.3f},{node['y']:.3f}) -> 像素({px},{py})")
        lines.append("=" * 60)
        return "\n".join(lines)
    
    def _get_font(self, size=14):
        """获取中文字体"""
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyhbd.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        ]
        for fp in font_paths:
            if os.path.exists(fp):
                try:
                    return ImageFont.truetype(fp, size)
                except:
                    continue
        return ImageFont.load_default()
    
    def _draw_legend(self, draw, font):
        """绘制图例"""
        legend_x = 20
        legend_y = self.map_height - 200
        box_width = 140
        box_height = 180
        
        # 背景框
        draw.rectangle(
            [legend_x, legend_y, legend_x + box_width, legend_y + box_height],
            fill=(255, 255, 255, 220),
            outline='black'
        )
        
        # 标题
        draw.text((legend_x + 10, legend_y + 5), '图例 Legend', fill='black', font=font)
        draw.line([(legend_x + 5, legend_y + 25), (legend_x + box_width - 5, legend_y + 25)], fill='black')
        
        # 各类别
        y_offset = 30
        for cat, color in self.CATEGORY_COLORS.items():
            cy = legend_y + y_offset
            draw.ellipse(
                [legend_x + 10, cy, legend_x + 24, cy + 14],
                fill=color,
                outline='white'
            )
            draw.text((legend_x + 28, cy), self.CATEGORY_NAMES.get(cat, cat), fill='black', font=font)
            y_offset += 22
    
    def _draw_arrow(self, draw, x1, y1, x2, y2, color):
        """在线段中点绘制方向箭头"""
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        angle = np.arctan2(y2 - y1, x2 - x1)
        
        arrow_len = 10
        arrow_angle = np.pi / 6
        
        ax1 = mx - arrow_len * np.cos(angle - arrow_angle)
        ay1 = my - arrow_len * np.sin(angle - arrow_angle)
        ax2 = mx - arrow_len * np.cos(angle + arrow_angle)
        ay2 = my - arrow_len * np.sin(angle + arrow_angle)
        
        draw.polygon([(mx, my), (ax1, ay1), (ax2, ay2)], fill=color)


def demo():
    """
    演示程序：完整展示地图标注和路径绘制功能
    """
    print("北京大学校园地图节点映射系统 - 演示")
    print("=" * 60)
    
    # 初始化映射器
    mapper = PKUMapMapper()
    
    # 打印映射摘要
    print(mapper.get_mapping_summary())
    
    # 1. 生成全节点标注地图
    print("\n[1] 生成全节点标注地图...")
    annotated_path = mapper.annotate_map(
        output_path=str(Path(mapper.map_path).parent / 'annotated_map.png'),
        show_labels=True
    )
    print(f"    结果: {annotated_path}")
    
    # 2. 绘制示例路径（校园经典游览路线）
    print("\n[2] 绘制校园经典游览路线...")
    # 西门 -> 未名湖 -> 博雅塔 -> 图书馆 -> 蔡元培像 -> 南门
    classic_route = [1, 8, 9, 10, 13, 5]
    path_path = mapper.draw_path(
        node_ids=classic_route,
        output_path=str(Path(mapper.map_path).parent / 'classic_route.png'),
        path_color='#FF0066',
        path_width=6
    )
    print(f"    经典路线 (西门→未名湖→博雅塔→图书馆→蔡元培像→南门)")
    print(f"    结果: {path_path}")
    
    # 3. 绘制园林游览路线
    print("\n[3] 绘制园林游览路线...")
    garden_route = [22, 23, 26, 27, 21, 17, 8, 19, 24]
    garden_path = mapper.draw_path(
        node_ids=garden_route,
        output_path=str(Path(mapper.map_path).parent / 'garden_route.png'),
        path_color='#228B22',
        path_width=6
    )
    print(f"    园林路线 (蔚秀园→承泽园→鸣鹤园→镜春园→朗润园→红湖→未名湖→勺园→畅春园)")
    print(f"    结果: {garden_path}")
    
    # 4. 节点查询演示
    print("\n[4] 节点查询演示...")
    queries = [9, "未名湖", "图书馆", "West Gate"]
    for q in queries:
        result = mapper.query_node(q)
        if result:
            px, py = result['pixel_coords']
            print(f"    查询 '{q}': 节点{result['node_id']} {result['name']} @ ({px}, {py})")
        else:
            print(f"    查询 '{q}': 未找到")
    
    # 5. 按类别列出节点
    print("\n[5] 校门节点列表:")
    gates = mapper.list_nodes_by_category('gate')
    for g in gates:
        print(f"    节点{g['node_id']}: {g['name']} ({g['name_en']})")
    
    print("\n" + "=" * 60)
    print("演示完成！所有输出文件保存在同一目录下。")
    print("=" * 60)
    
    return mapper


if __name__ == '__main__':
    mapper = demo()
