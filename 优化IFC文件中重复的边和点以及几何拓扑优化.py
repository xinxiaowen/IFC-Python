import argparse
import os
from dataclasses import dataclass, field
from typing import List, Dict, Set
import math
import re

@dataclass
class IfcEntity:
    id: int
    type: str
    raw: str
    refs: List[int] = field(default_factory=list)

def parse_ifc_file(file_path: str):
    entities: List[IfcEntity] = []
    forward_refs: Dict[int, List[int]] = {}
    reverse_refs: Dict[int, List[int]] = {}
    header_lines: List[str] = []
    footer_lines: List[str] = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        in_data_section = False
        data_section_ended = False
        buffer = ""
        for line in f:
            line_strip = line.rstrip('\n')
            if not in_data_section:
                if not data_section_ended:
                    # 收集HEADER部分的行
                    if line_strip.strip().upper() == "DATA;":
                        header_lines.append(line_strip)
                        in_data_section = True
                        buffer = ""
                        continue
                    else:
                        header_lines.append(line_strip)
                        continue
                else:
                    # DATA部分结束后，收集FOOTER部分的行
                    footer_lines.append(line_strip)
                    continue
            # 解析DATA部分的实体
            if line_strip.strip().upper() == "ENDSEC;":
                footer_lines.append(line_strip)
                in_data_section = False
                data_section_ended = True
                buffer = ""
                continue
            part = line_strip.strip()
            if part == '':
                continue
            while True:
                idx = part.find(';')
                if idx == -1:
                    buffer += part + " "
                    break
                entity_str = buffer + part[:idx+1]
                entity_str = entity_str.strip()
                if entity_str != "":  # 解析单个实体定义
                    eq_idx = entity_str.find('=')
                    paren_idx = entity_str.find('(')
                    if eq_idx != -1 and paren_idx != -1 and entity_str.startswith('#'):
                        try:
                            ent_id = int(entity_str[1:eq_idx])
                        except:
                            ent_id = None
                        ent_type = entity_str[eq_idx+1:paren_idx].strip()
                        if ent_id is not None and ent_type:
                            ent = IfcEntity(id=ent_id, type=ent_type, raw=entity_str)
                            # 去除引号内内容，以避免错误识别引用
                            attr_str = entity_str[eq_idx+1:]
                            cleaned_chars = []
                            i = 0
                            inside_quote = False
                            while i < len(attr_str):
                                ch = attr_str[i]
                                if ch == "'":
                                    if inside_quote:
                                        if i+1 < len(attr_str) and attr_str[i+1] == "'":
                                            i += 2
                                            continue  # 跳过转义的单引号
                                        else:
                                            inside_quote = False
                                            i += 1
                                            continue
                                    else:
                                        inside_quote = True
                                        i += 1
                                        continue
                                if inside_quote:
                                    i += 1
                                else:
                                    cleaned_chars.append(ch)
                                    i += 1
                            cleaned_str = "".join(cleaned_chars)
                            # 找出所有引用的实体ID
                            refs: List[int] = []
                            for m in re.finditer(r'\#(\d+)', cleaned_str):
                                rid_str = m.group(1)
                                if rid_str:
                                    try:
                                        rid = int(rid_str)
                                        if rid != ent_id:
                                            refs.append(rid)
                                    except:
                                        continue
                            ent.refs = refs
                            forward_refs[ent.id] = refs
                            for rid in refs:
                                reverse_refs.setdefault(rid, []).append(ent.id)
                            entities.append(ent)
                part = part[idx+1:].lstrip()
                buffer = ""
                if part == "":
                    break
    return entities, header_lines, footer_lines, forward_refs, reverse_refs

def optimize_ifc(entities: List[IfcEntity], forward_refs: Dict[int, List[int]], reverse_refs: Dict[int, List[int]], simplify_geometry: bool=False, tol: float=1e-6):
    original_count = len(entities)
    duplicate_merge_count = 0
    polyline_points_removed = 0
    entities_by_id: Dict[int, IfcEntity] = {ent.id: ent for ent in entities}
    # 合并重复的 IfcCartesianPoint
    coord_map: Dict[tuple, int] = {}
    duplicate_map: Dict[int, int] = {}
    for ent in entities:
        if ent.type.upper() == "IFCCARTESIANPOINT":
            match = re.search(r'IFCCARTESIANPOINT\(\(\s*(.*?)\s*\)\)', ent.raw, re.IGNORECASE)
            coord_str = match.group(1) if match else ""
            if coord_str == "":
                continue
            coords = [c.strip() for c in coord_str.split(',') if c.strip() != "" and c.strip() != "$"]
            vals: List[float] = []
            for c in coords:
                try:
                    vals.append(float(c))
                except:
                    try:
                        vals.append(float(c.replace('D', 'e').replace('d', 'e')))
                    except:
                        vals.append(0.0)
            if len(vals) == 0:
                continue
            if len(vals) == 2:
                vals.append(0.0)  # 确保有三维坐标
            key = tuple(round(v, 6) for v in vals)  # 根据容差取整作为重复判断
            if key in coord_map:
                kept_id = coord_map[key]
                duplicate_map[ent.id] = kept_id
            else:
                coord_map[key] = ent.id
    # 处理嵌套的重复映射关系
    for old, new in list(duplicate_map.items()):
        final_new = new
        while final_new in duplicate_map:
            final_new = duplicate_map[final_new]
        duplicate_map[old] = final_new
    duplicate_merge_count = len(duplicate_map)
    if duplicate_merge_count > 0:
        # 替换所有对重复点的引用为保留的点
        for ent in entities:
            if not ent.refs:
                continue
            for old_id, new_id in duplicate_map.items():
                if old_id in ent.refs:
                    ent.raw = re.sub(rf'\#{old_id}(?=[^0-9])', f'#{new_id}', ent.raw)
        # 从实体列表中移除重复的点实体
        entities = [ent for ent in entities if ent.id not in duplicate_map]
        for old_id in duplicate_map:
            entities_by_id.pop(old_id, None)
    # 简化几何结构：合并 IfcPolyline 中共线的连续点
    if simplify_geometry:
        for ent in entities:
            if ent.type.upper() == "IFCPOLYLINE":
                match = re.search(r'IFCPOLYLINE\(\(\s*(.*?)\s*\)\)', ent.raw, re.IGNORECASE)
                if not match:
                    continue
                list_str = match.group(1)
                if list_str.strip() == "":
                    continue
                point_ids = [int(x.strip()[1:]) for x in list_str.split(',') if x.strip().startswith('#')]
                if not point_ids or len(point_ids) < 2:
                    continue
                # 应用重复点映射，确保点列表使用更新后的ID
                if duplicate_merge_count > 0:
                    point_ids = [duplicate_map.get(pid, pid) for pid in point_ids]
                # 去除连续重复的点
                j = 0
                while j < len(point_ids) - 1:
                    if point_ids[j] == point_ids[j+1]:
                        point_ids.pop(j+1)
                        polyline_points_removed += 1
                    else:
                        j += 1
                if len(point_ids) < 3:
                    # 少于3个点，无需进一步处理，直接更新实体
                    new_list_str = ",".join(f"#{pid}" for pid in point_ids)
                    ent.raw = f"#{ent.id}={ent.type}(({new_list_str}));"
                    ent.refs = [pid for pid in point_ids]
                    continue
                # 函数：获取指定点的坐标
                def get_coords(pid: int):
                    if pid not in entities_by_id:
                        return None
                    p_ent = entities_by_id[pid]
                    m = re.search(r'IFCCARTESIANPOINT\(\(\s*(.*?)\s*\)\)', p_ent.raw, re.IGNORECASE)
                    if not m:
                        return None
                    cstr = m.group(1)
                    comps = [comp.strip() for comp in cstr.split(',') if comp.strip() not in ("", "$")]
                    vals = []
                    for comp in comps:
                        try:
                            vals.append(float(comp))
                        except:
                            try:
                                vals.append(float(comp.replace('D', 'e').replace('d', 'e')))
                            except:
                                return None
                    if len(vals) == 2:
                        vals.append(0.0)
                    if len(vals) == 0:
                        return None
                    return vals
                # 删除共线且在中间的点
                i = 0
                while i < len(point_ids) - 2:
                    pidA, pidB, pidC = point_ids[i], point_ids[i+1], point_ids[i+2]
                    coordsA = get_coords(pidA)
                    coordsB = get_coords(pidB)
                    coordsC = get_coords(pidC)
                    if coordsA is None or coordsB is None or coordsC is None:
                        i += 1
                        continue
                    ax, ay, az = coordsA[0], coordsA[1], coordsA[2] if len(coordsA) > 2 else 0.0
                    bx, by, bz = coordsB[0], coordsB[1], coordsB[2] if len(coordsB) > 2 else 0.0
                    cx, cy, cz = coordsC[0], coordsC[1], coordsC[2] if len(coordsC) > 2 else 0.0
                    # 计算AB和AC的叉乘向量
                    AB = (bx - ax, by - ay, bz - az)
                    AC = (cx - ax, cy - ay, cz - az)
                    cross = (AB[1]*AC[2] - AB[2]*AC[1],
                             AB[2]*AC[0] - AB[0]*AC[2],
                             AB[0]*AC[1] - AB[1]*AC[0])
                    cross_mag_sq = cross[0]**2 + cross[1]**2 + cross[2]**2
                    if cross_mag_sq < 1e-12:  # 三点共线
                        AB_len = math.sqrt(AB[0]**2 + AB[1]**2 + AB[2]**2)
                        BC = (cx - bx, cy - by, cz - bz)
                        BC_len = math.sqrt(BC[0]**2 + BC[1]**2 + BC[2]**2)
                        AC_len = math.sqrt(AC[0]**2 + AC[1]**2 + AC[2]**2)
                        # 检查B点是否在AC直线上且介于A和C之间
                        if abs((AB_len + BC_len) - AC_len) < 1e-6:
                            point_ids.pop(i+1)
                            polyline_points_removed += 1
                            continue  # 继续检查新的三元组（A与移除后的下一点）
                    i += 1
                # 更新Polyline的实体定义
                new_list_str = ",".join(f"#{pid}" for pid in point_ids)
                ent.raw = f"#{ent.id}={ent.type}(({new_list_str}));"
                ent.refs = [pid for pid in point_ids]
    # 重新计算引用关系（正向和逆向）以识别未被引用的实体
    forward_refs.clear()
    reverse_refs.clear()
    for ent in entities:
        eq_idx = ent.raw.find('=')
        attr_str = ent.raw[eq_idx+1:] if eq_idx != -1 else ent.raw
        cleaned_chars = []
        i = 0
        inside_quote = False
        while i < len(attr_str):
            ch = attr_str[i]
            if ch == "'":
                if inside_quote:
                    if i+1 < len(attr_str) and attr_str[i+1] == "'":
                        i += 2
                        continue
                    else:
                        inside_quote = False
                        i += 1
                        continue
                else:
                    inside_quote = True
                    i += 1
                    continue
            if inside_quote:
                i += 1
            else:
                cleaned_chars.append(ch)
                i += 1
        cleaned_str = "".join(cleaned_chars)
        refs: List[int] = []
        for m in re.finditer(r'\#(\d+)', cleaned_str):
            rid_str = m.group(1)
            if rid_str:
                try:
                    rid = int(rid_str)
                    if rid != ent.id:
                        refs.append(rid)
                except:
                    continue
        ent.refs = refs
        forward_refs[ent.id] = refs
        for rid in refs:
            reverse_refs.setdefault(rid, []).append(ent.id)
    # 使用深度优先搜索，从 IfcProject/IfcProjectLibrary 出发，标记需要保留的实体
    start_ids = [ent.id for ent in entities if ent.type.upper() in ("IFCPROJECT", "IFCPROJECTLIBRARY")]
    visited: Set[int] = set()
    stack = start_ids.copy() if start_ids else []
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        for rid in forward_refs.get(cur, []):
            if rid not in visited:
                stack.append(rid)
        for rid in reverse_refs.get(cur, []):
            if rid not in visited:
                stack.append(rid)
    if not start_ids:
        visited = {ent.id for ent in entities}
    # 按原始顺序收集保留的实体
    kept_entities = [ent for ent in entities if ent.id in visited]
    final_count = len(kept_entities)
    removed_count = original_count - final_count
    return kept_entities, removed_count, duplicate_merge_count, polyline_points_removed

# === 用户可修改的配置 ===========================
INPUT_IFC_PATH   = r"D:\Python案例\IFC文件体积优化\2022020320211122Wellness center Sama_WX.ifc"          # 输入 IFC
OUTPUT_IFC_PATH  = r"D:\Python案例\IFC文件体积优化\2022020320211122Wellness center Sama_WX1.ifc"  # 输出 IFC
SIMPLIFY_GEOMETRY = True   # 是否执行 IfcPolyline 冗余点/共线点清理
# ================================================

def main():
    # 解析
    entities, header, footer, fwd, rev = parse_ifc_file(INPUT_IFC_PATH)

    # 优化
    kept, removed_cnt, dup_pt_cnt, polyline_fix_cnt = optimize_ifc(
        entities, fwd, rev, simplify_geometry=SIMPLIFY_GEOMETRY
    )

    # 写回
    with open(OUTPUT_IFC_PATH, "w", encoding="utf-8") as fp:
        fp.write("\n".join(header) + "\n")
        for ent in kept:
            fp.write(ent.raw + "\n")
        fp.write("\n".join(footer) + "\n")

    # 控制台统计信息
    print(f"原实体数:      {len(entities)}")
    print(f"已删除实体数:  {removed_cnt}")
    print(f"合并点数量:    {dup_pt_cnt}")
    if SIMPLIFY_GEOMETRY:
        print(f"Polyline 冗余点删除: {polyline_fix_cnt}")

if __name__ == "__main__":
    main()
