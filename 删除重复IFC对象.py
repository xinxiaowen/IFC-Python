#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ======== 在此直接指定 IFC 输入 / 输出 文件路径 =========
INPUT_IFC  = r"D:\Python案例\IFC文件体积优化\2022020320211122Wellness center Sama_WX.ifc"          # 原 IFC 文件
OUTPUT_IFC = r"D:\Python案例\IFC文件体积优化\2022020320211122Wellness center Sama_WX_duplicate.ifc"    # 去重后 IFC 文件
# =====================================================

# ---------- 核心去重函数 ----------
def remove_duplicates_from_ifc(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as fp:
        content = fp.read()

    idx_data = content.find("DATA;")
    idx_end  = content.find("ENDSEC;", idx_data)
    if idx_data == -1 or idx_end == -1:
        print("无法找到 DATA 区段，文件格式异常")
        return

    header = content[:idx_data + len("DATA;")]
    data   = content[idx_data + len("DATA;"): idx_end]
    tail   = content[idx_end:]

    if header and header[-1] != "\n":
        header += "\n"

    # --- 将 DATA 段拆分成实体列表 ---
    entities = []
    buf, in_str, depth = "", False, 0
    i = 0
    while i < len(data):
        ch = data[i]
        if not in_str:
            if ch == "'":
                in_str = True
                buf += ch
            elif ch == "(":
                depth += 1
                buf += ch
            elif ch == ")":
                depth -= 1
                buf += ch
            elif ch == ";":
                if depth == 0:
                    ent = buf.strip()
                    if ent:
                        entities.append(ent)
                    buf = ""
                else:
                    buf += ch
            elif ch.isspace():
                # 去掉参数间多余空白
                pass
            else:
                buf += ch
        else:
            if ch == "'":
                # 处理 '' 转义
                if i + 1 < len(data) and data[i + 1] == "'":
                    buf += "'"
                    i += 1
                else:
                    in_str = False
                    buf += ch
            else:
                buf += ch
        i += 1
    if buf.strip():
        entities.append(buf.strip())

    # --------- 迭代去重 ----------
    removed_total, removed_by_type = 0, {}
    while True:
        key2id, dup_map = {}, {}
        for ent in entities:
            eq = ent.find("=")
            if eq == -1:
                continue
            ent_id = int(ent[1:eq])
            paren = ent.find("(", eq)
            etype = ent[eq + 1 : paren].strip().upper()
            params = ent[paren:]    # 含括号
            key = (etype, params.replace(" ", "").replace("\n", ""))
            if key in key2id:
                dup_map[ent_id] = key2id[key]
                removed_by_type[etype] = removed_by_type.get(etype, 0) + 1
            else:
                key2id[key] = ent_id
        if not dup_map:
            break  # 无更多重复

        # 替换引用并删除重复实体
        new_entities = []
        for ent in entities:
            eq = ent.find("=")
            ent_id = int(ent[1:eq])
            if ent_id in dup_map:   # 跳过重复
                continue
            lhs = ent[: eq + 1]
            rhs = ent[eq + 1 :]
            out, j, in_s = "", 0, False
            while j < len(rhs):
                c = rhs[j]
                if not in_s:
                    if c == "'":
                        in_s = True
                        out += c
                    elif c == "#":
                        k = j + 1
                        rid_str = ""
                        while k < len(rhs) and rhs[k].isdigit():
                            rid_str += rhs[k]
                            k += 1
                        if rid_str:
                            rid = int(rid_str)
                            rid = dup_map.get(rid, rid)
                            out += f"#{rid}"
                            j = k - 1
                        else:
                            out += c
                    else:
                        out += c
                else:
                    if c == "'":
                        if j + 1 < len(rhs) and rhs[j + 1] == "'":
                            out += "'"
                            j += 1
                        else:
                            in_s = False
                            out += c
                    else:
                        out += c
                j += 1
            new_entities.append(lhs + out)
        entities = new_entities
        removed_total += len(dup_map)

    # ------- 写出新的 IFC ----------
    with open(output_path, "w", encoding="utf-8") as fw:
        fw.write(header)
        for ent in entities:
            fw.write(ent + ";\n")
        fw.write(tail.lstrip())

    # ------- 控制台统计 ----------
    print(f"\n重复实体已删除: {removed_total}")
    for tp, cnt in removed_by_type.items():
        print(f"  {tp:<25}: {cnt}")

# 直接调用，使用上面固定的文件路径
remove_duplicates_from_ifc(INPUT_IFC, OUTPUT_IFC)
