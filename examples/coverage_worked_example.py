"""Coverage honesty, worked end to end.

Companion to the write-up "The unmapped majority"
(https://www.jayeshsuryavanshi.com/blog/geosocialx-coverage.html).

Builds a seeded, synthetic San-Francisco X-API-v2 corpus calibrated to the
documented sparsity of geotagged social data (a small fraction with exact
coordinates, a modest slice with only a place tag, and a large no-location
remainder), then runs the shipping GeoSocialX API to show the core idea:

  * ``coverage()`` reports exact / place-only / no-geo *before* you map anything;
  * ``extract_points(tweets)`` is the naive map, exact coordinates only;
  * ``extract_points(tweets, places=...)`` recovers ~10x more by resolving place
    tags to their bounding-box centroid, and flags each point's ``source``.

Run it for the numbers with nothing but the package installed::

    pip install geosocialx
    python coverage_worked_example.py

Install the ``matplotlib`` extra as well and it also renders the two figures
from the post (``geosocialx-coverage.png`` and ``geosocialx-maps.png``) into the
current directory.
"""

from __future__ import annotations

import random
from collections import Counter
from pathlib import Path

from geosocialx import GeospatialAnalyzer, GeospatialExtractor, __version__

# 20 SF neighborhoods (name -> centre lon/lat); place bbox = centre +/- 0.006 deg.
HOODS = {
    "Mission": (-122.4190, 37.7600),
    "SoMa": (-122.4010, 37.7785),
    "Financial District": (-122.3999, 37.7946),
    "North Beach": (-122.4100, 37.8000),
    "Castro": (-122.4350, 37.7620),
    "Haight-Ashbury": (-122.4460, 37.7690),
    "Marina": (-122.4360, 37.8030),
    "Sunset": (-122.4950, 37.7520),
    "Richmond": (-122.4830, 37.7800),
    "Nob Hill": (-122.4140, 37.7930),
    "Chinatown": (-122.4070, 37.7940),
    "Tenderloin": (-122.4130, 37.7840),
    "Hayes Valley": (-122.4240, 37.7760),
    "Pacific Heights": (-122.4360, 37.7920),
    "Bernal Heights": (-122.4160, 37.7390),
    "Potrero Hill": (-122.4000, 37.7590),
    "Dogpatch": (-122.3880, 37.7580),
    "Excelsior": (-122.4300, 37.7240),
    "Glen Park": (-122.4340, 37.7340),
    "Presidio": (-122.4660, 37.7980),
}
PLACES = {
    name: [lon - 0.006, lat - 0.006, lon + 0.006, lat + 0.006]
    for name, (lon, lat) in HOODS.items()
}
WEIGHTS = {
    "Mission": 12,
    "SoMa": 11,
    "Financial District": 9,
    "North Beach": 7,
    "Castro": 6,
    "Haight-Ashbury": 5,
    "Marina": 6,
    "Sunset": 3,
    "Richmond": 3,
    "Nob Hill": 4,
    "Chinatown": 5,
    "Tenderloin": 4,
    "Hayes Valley": 4,
    "Pacific Heights": 4,
    "Bernal Heights": 2,
    "Potrero Hill": 3,
    "Dogpatch": 3,
    "Excelsior": 2,
    "Glen Park": 2,
    "Presidio": 3,
}

N_EXACT, N_PLACE, N_NOGEO = 80, 720, 4200  # 1.6% / 14.4% / 84.0% of 5,000

# exact-coordinate blobs (people geotag most where they gather)
BLOBS = [
    ((-122.4190, 37.7600), 0.010, 22),
    ((-122.4005, 37.7880), 0.011, 20),
    ((-122.4360, 37.8020), 0.008, 12),
    ((-122.4350, 37.7620), 0.007, 10),
    ((-122.4700, 37.7650), 0.014, 9),
    ((-122.4100, 37.8000), 0.006, 7),
]


def build_corpus(seed: int = 20260731) -> tuple[list[dict], list[tuple[float, float]]]:
    """Return (tweets, exact_points): X-API-v2-shaped dicts, deterministically."""
    rng = random.Random(seed)

    def a_time() -> str:
        day = rng.randint(21, 27)
        hour = rng.choice(
            [9, 10, 11, 12, 13, 17, 18, 19, 20, 21, 22, 8, 14, 15, 16, 23]
        )
        return f"2026-07-{day:02d}T{hour:02d}:{rng.randint(0, 59):02d}:00.000Z"

    tweets: list[dict] = []
    tid = 10_000

    exact_pts: list[tuple[float, float]] = []
    for (clon, clat), sd, k in BLOBS:
        for _ in range(k):
            exact_pts.append((clon + rng.gauss(0, sd), clat + rng.gauss(0, sd * 0.8)))
    exact_pts = exact_pts[:N_EXACT]
    for lon, lat in exact_pts:
        tid += 1
        tweets.append(
            {
                "id": tid,
                "text": "…",
                "created_at": a_time(),
                "author_id": tid,
                "geo": {"coordinates": {"type": "Point", "coordinates": [lon, lat]}},
            }
        )

    names, weights = list(WEIGHTS), [WEIGHTS[h] for h in WEIGHTS]
    for _ in range(N_PLACE):
        tid += 1
        hood = rng.choices(names, weights=weights, k=1)[0]
        tweets.append(
            {
                "id": tid,
                "text": "…",
                "created_at": a_time(),
                "author_id": tid,
                "geo": {"place_id": hood},
            }
        )

    for _ in range(N_NOGEO):
        tid += 1
        tweets.append(
            {"id": tid, "text": "…", "created_at": a_time(), "author_id": tid}
        )

    rng.shuffle(tweets)
    return tweets, exact_pts


def main() -> None:
    tweets, _ = build_corpus()
    ex = GeospatialExtractor()

    cov = ex.coverage(tweets)
    naive = ex.extract_points(tweets)
    honest = ex.extract_points(tweets, places=PLACES)
    an = GeospatialAnalyzer(honest)

    print(f"geosocialx {__version__}")
    print("coverage       :", cov)
    print(f"naive points   : {len(naive)} ({len(naive) / cov['total']:.1%})")
    print(f"honest points  : {len(honest)} ({len(honest) / cov['total']:.1%})")
    print(f"  of which place: {sum(p.source == 'place' for p in honest)}")
    print(f"recovery factor: {len(honest) / max(len(naive), 1):.1f}x")
    print("summary        :", an.summary())
    print("top hotspots   :", an.densest_cells(cell_size_deg=0.01, top=5))
    print("posts / day    :", an.time_bins("day"))

    try:
        import matplotlib  # noqa: F401
    except ImportError:
        print("\n(install matplotlib to also render the two figures)")
        return
    _render_figures(cov, naive, honest, Path.cwd())


def _render_figures(cov: dict, naive: list, honest: list, out_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.lines import Line2D
    from matplotlib.patches import Polygon as MplPolygon

    paper, ink, ink_soft, rule = "#faf8f3", "#22201b", "#57534a", "#e3ddce"
    accent, rust, dark = "#204a87", "#9c531f", "#cfc8b8"
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Georgia", "Charter", "DejaVu Serif"],
            "text.color": ink,
            "axes.edgecolor": rule,
            "figure.facecolor": paper,
            "axes.facecolor": paper,
            "savefig.facecolor": paper,
        }
    )

    # figure 1: the coverage cliff
    fig, ax = plt.subplots(figsize=(9.2, 2.9))
    total, left = cov["total"], 0
    for n, color in (
        (cov["with_point"], accent),
        (cov["place_only"], rust),
        (cov["no_geo"], dark),
    ):
        ax.barh(
            0, n, left=left, height=0.5, color=color, edgecolor=paper, linewidth=1.2
        )
        if n / total > 0.04:
            ax.text(
                left + n / 2,
                0,
                f"{n / total:.0%}",
                ha="center",
                va="center",
                color=(paper if color != dark else ink_soft),
                fontsize=13,
                fontweight="bold",
            )
        left += n
    ax.annotate(
        f"exact coordinates\n{cov['with_point']:,} posts · 1.6%",
        xy=(cov["with_point"] / 2, -0.28),
        xytext=(total * 0.06, -0.95),
        ha="left",
        va="top",
        color=accent,
        fontsize=10.5,
        arrowprops=dict(arrowstyle="-", color=accent, lw=1),
    )
    ax.plot([0, cov["with_point"]], [0.34, 0.34], color=accent, lw=1)
    ax.text(
        cov["with_point"] / 2,
        0.44,
        "what a naive map keeps: 1.6%",
        ha="left",
        va="bottom",
        color=accent,
        fontsize=10.5,
    )
    mapp = cov["with_point"] + cov["place_only"]
    ax.plot([0, mapp], [0.62, 0.62], color=rust, lw=1)
    ax.text(
        mapp + total * 0.006,
        0.62,
        "mappable with place-resolution: 16%  (10x more)",
        ha="left",
        va="center",
        color=rust,
        fontsize=10.5,
    )
    ax.text(
        total - cov["no_geo"] / 2,
        -0.42,
        "84%, reported by coverage(), not silently dropped",
        ha="center",
        va="top",
        color=ink_soft,
        fontsize=10.5,
    )
    ax.set_xlim(-total * 0.01, total * 1.02)
    ax.set_ylim(-1.15, 0.9)
    ax.axis("off")
    ax.set_title(
        "One realistic city pull of 5,000 posts, sorted by the location they carry",
        color=ink,
        fontsize=12.5,
        fontweight="bold",
        loc="left",
        pad=14,
    )
    fig.tight_layout()
    fig.savefig(
        out_dir / "geosocialx-coverage.png",
        dpi=200,
        bbox_inches="tight",
        pad_inches=0.18,
    )
    plt.close(fig)

    # figure 2: same corpus, two maps
    outline = [
        (-122.5107, 37.7080),
        (-122.5136, 37.7770),
        (-122.5090, 37.7900),
        (-122.4780, 37.8110),
        (-122.4450, 37.8080),
        (-122.4190, 37.8090),
        (-122.4030, 37.8080),
        (-122.3980, 37.8060),
        (-122.3770, 37.8080),
        (-122.3820, 37.7900),
        (-122.3870, 37.7660),
        (-122.3770, 37.7400),
        (-122.3830, 37.7200),
        (-122.4050, 37.7080),
    ]
    extent = (-122.525, -122.365, 37.700, 37.820)

    def basemap(ax):
        ax.add_patch(
            MplPolygon(
                outline,
                closed=True,
                facecolor="#f0eadd",
                edgecolor=rule,
                linewidth=1.0,
                zorder=0,
            )
        )
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_aspect(1.0 / np.cos(np.radians(37.76)))
        for s in ax.spines.values():
            s.set_color(rule)
        ax.set_xticks([])
        ax.set_yticks([])
        dlon = 2.0 / (111.32 * np.cos(np.radians(37.76)))
        ax.plot(
            [-122.520, -122.520 + dlon],
            [37.706, 37.706],
            color=ink_soft,
            lw=2,
            zorder=5,
        )
        ax.text(
            -122.520 + dlon / 2,
            37.709,
            "2 km",
            ha="center",
            va="bottom",
            color=ink_soft,
            fontsize=8,
        )

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 4.5))
    for ax in (axL, axR):
        basemap(ax)
    xs = [p.longitude for p in naive]
    ys = [p.latitude for p in naive]
    axL.scatter(
        xs, ys, s=16, color=accent, alpha=0.85, edgecolor=paper, linewidth=0.4, zorder=4
    )
    axL.set_title(
        f"Exact coordinates only\n{len(naive)} points · 1.6% of the corpus",
        color=ink,
        fontsize=11.5,
        fontweight="bold",
        pad=8,
    )
    counts = Counter(
        (round(p.longitude, 4), round(p.latitude, 4))
        for p in honest
        if p.source == "place"
    )
    for (lon, lat), c in counts.items():
        axR.scatter(
            lon,
            lat,
            s=18 * np.sqrt(c),
            facecolor="none",
            edgecolor=rust,
            linewidth=1.4,
            alpha=0.9,
            zorder=3,
        )
    axR.scatter(
        xs, ys, s=16, color=accent, alpha=0.85, edgecolor=paper, linewidth=0.4, zorder=4
    )
    axR.set_title(
        f"+ place-resolution\n{len(honest)} points · 16% · rings = coarse centroids",
        color=ink,
        fontsize=11.5,
        fontweight="bold",
        pad=8,
    )
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=accent,
            markeredgecolor=paper,
            markersize=7,
            label="exact coordinate",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor="none",
            markeredgecolor=rust,
            markersize=10,
            markeredgewidth=1.4,
            label="place centroid (bigger = more posts)",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=9.5,
        bbox_to_anchor=(0.5, -0.02),
        labelcolor=ink_soft,
    )
    fig.suptitle(
        "Same 5,000 posts, two maps: the honest one is fuller but coarser",
        color=ink,
        fontsize=12.5,
        fontweight="bold",
        x=0.02,
        ha="left",
        y=1.02,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(
        out_dir / "geosocialx-maps.png", dpi=200, bbox_inches="tight", pad_inches=0.18
    )
    plt.close(fig)
    print(f"\nwrote geosocialx-coverage.png and geosocialx-maps.png to {out_dir}")


if __name__ == "__main__":
    main()
