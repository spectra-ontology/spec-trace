"""RQ1 의 '정답이 문맥에 담긴 문항 수'를 접근 경로별 가로 막대로 그리는 TikZ 그림을 만든다.

usage: make_access_figure.py <out tex>
값은 본문 RQ1 문단과 verify_section_6.py 가 읽는 두 측정 파일에서만 가져온다.
  final/text_route_ceiling/ceiling.json  경로별 담긴 문항 수(groups[0] = 정답 있는 581문항 전체)
  final/dense_ceiling_by_k.json          밀집 검색 청크 수별 담긴 문항 수
설정이 여럿인 경로는 짙은 부분이 그 설정들 가운데 가장 적은 문항 수, 옅은 연장이 가장 많은 문항 수까지다. check_vldb_text.py 가
같은 함수로 그림을 다시 만들어 원고에 들어간 그림과 견준다."""
import json
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
L = ROOT / "logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark"

# (그림의 줄 이름, 가장 작은 설정의 값, 가장 큰 설정의 값)
def rows(ceiling, by_k):
    group = ceiling["groups"][0]
    assert group["value"] == "all" and group["n"] == 581, (group["value"], group["n"])
    r = group["routes"]
    k = by_k["groups"][0]["byK"]
    ids = [r[x]["allRows"] for x in ("idkey_1500", "idkey_full", "idany_1500", "idany_full")]
    return group["n"], [
        ("Dense, 8 chunks", k["8"]["meta"]["allRows"], k["8"]["meta"]["allRows"]),
        ("Dense, 256 chunks", k["256"]["meta"]["allRows"], k["256"]["meta"]["allRows"]),
        ("BM25 on question words", r["bm25_8x1500"]["allRows"], r["bm25_12x4000"]["allRows"]),
        ("Rank fusion of the two", r["rrf_8x1500"]["allRows"], r["rrf_12x4000"]["allRows"]),
        ("Chunks of question identifiers", min(ids), max(ids)),
        ("Identifiers followed once more", r["hopkey_1500"]["allRows"], r["hopkey_full"]["allRows"]),
    ]


def load():
    ceiling = json.loads((L / "final/text_route_ceiling/ceiling.json").read_text(encoding="utf-8"))
    by_k = json.loads((L / "final/dense_ceiling_by_k.json").read_text(encoding="utf-8"))
    return ceiling, by_k


def figure_tex(ceiling, by_k):
    n, data = rows(ceiling, by_k)
    width = 4.3  # cm for n items
    scale = width / n
    step = 0.42
    out = [
        "\\begin{figure}[t]",
        "\\centering",
        "\\begin{tikzpicture}[font=\\footnotesize]",
    ]
    for i, (name, lo, hi) in enumerate(data):
        y = -i * step
        out.append(f"\\node[anchor=east, inner sep=0pt] at (-0.12,{y:.2f}) {{{name}}};")
        if hi > lo:
            out.append(f"\\fill[SpineFill, draw=SpineStroke, line width=0.4pt] ({lo * scale:.3f},{y - 0.13:.2f}) "
                       f"rectangle ({hi * scale:.3f},{y + 0.13:.2f});")
        if lo > 0:
            out.append(f"\\fill[SpineStroke] (0,{y - 0.13:.2f}) rectangle ({lo * scale:.3f},{y + 0.13:.2f});")
        label = str(lo) if lo == hi else f"{lo} to {hi}"
        out.append(f"\\node[anchor=west, inner sep=0pt, font=\\scriptsize] at ({hi * scale + 0.08:.3f},{y:.2f}) {{{label}}};")
    bottom = -(len(data) - 1) * step - 0.3
    out += [
        f"\\draw[SatStroke, line width=0.4pt] (0,0.3) -- (0,{bottom:.2f});",
        f"\\draw[SatStroke, dashed, line width=0.4pt] ({width:.3f},0.3) -- ({width:.3f},{bottom:.2f});",
        f"\\node[anchor=south, font=\\scriptsize, text=SatStroke] at ({width:.3f},0.3) {{all {n}}};",
        f"\\foreach \\v in {{0,200,400}} \\draw[SatStroke, line width=0.4pt] (\\v*{scale:.6f},{bottom:.2f}) -- ++(0,-0.06) "
        f"node[below, font=\\scriptsize, text=SatStroke, inner sep=1pt] {{\\v}};",
        f"\\node[anchor=north east, inner sep=0pt, font=\\scriptsize, text=SatStroke] at (-0.35,{bottom - 0.08:.2f}) "
        "{answerable items};",
        "\\end{tikzpicture}",
        "\\caption{Answerable items whose context holds every field of every gold row, by access path. "
        "Where a route has several settings (chunk count and length, key field or any mention), the dark bar "
        "ends at the lowest count over them and the light extension at the highest.}",
        "\\Description{Horizontal bars for six access paths. Dense retrieval contains 1 item at eight chunks and 7 at 256; "
        "BM25 contains 59 to 66; rank fusion of the two 19 to 40; the chunks of the question's identifiers 383 to 395; "
        "following the identifiers seen there once more 554 of the 581 answerable items.}",
        "\\label{fig:access}",
        "\\end{figure}",
        "",
    ]
    return "\n".join(out)


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(figure_tex(*load()), encoding="utf-8")
    print("written", sys.argv[1])
