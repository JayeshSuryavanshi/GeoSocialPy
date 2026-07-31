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
    from matplotlib.colors import ListedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Polygon as MplPolygon

    # simple sans typography + a maroon-aligned, colour-blind-legible palette
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica", "Arial", "DejaVu Sans"],
        }
    )
    PAPER = "#faf8f3"
    INK, SOFT, FAINT = "#20201e", "#565049", "#8a867a"
    RULE = "#d8d2c6"
    MAROON = "#7a1c2b"  # exact coordinates
    STEEL = "#4f6d8f"  # place tag only
    GRAY = "#cbc4b6"  # no location
    LAND = "#efe9dd"
    WATER = "#aec4d0"

    # ====================================================================
    # figure 1 : unit chart, one square per post
    # ====================================================================
    total = cov["total"]
    n_exact, n_place, n_nogeo = cov["with_point"], cov["place_only"], cov["no_geo"]
    cols = 100
    rows = total // cols
    cat = np.array([0] * n_exact + [1] * n_place + [2] * n_nogeo).reshape(rows, cols)

    fig = plt.figure(figsize=(9.4, 6.6))
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0.055, 0.205, 0.89, 0.63])
    ax.set_facecolor(PAPER)
    ax.pcolormesh(
        cat,
        cmap=ListedColormap([MAROON, STEEL, GRAY]),
        edgecolors=PAPER,
        linewidth=1.0,
    )
    ax.set_aspect("equal")
    ax.set_xlim(0, cols)
    ax.set_ylim(0, rows)
    ax.invert_yaxis()
    ax.axis("off")

    fig.text(
        0.055,
        0.935,
        "Where 5,000 posts actually carry a location",
        color=INK,
        fontsize=15,
        fontweight="bold",
        ha="left",
    )
    fig.text(
        0.055,
        0.888,
        "One square is one post, filled in blocks by the location it carries.",
        color=SOFT,
        fontsize=11,
        ha="left",
    )

    legend = [
        (MAROON, "exact coordinates", n_exact, "1.6%"),
        (STEEL, "place tag only", n_place, "14.4%"),
        (GRAY, "no location at all", n_nogeo, "84.0%"),
    ]
    for (color, name, n, pct), x in zip(legend, (0.055, 0.40, 0.71)):
        fig.patches.append(
            plt.Rectangle(
                (x, 0.083),
                0.017,
                0.028,
                transform=fig.transFigure,
                facecolor=color,
                edgecolor="none",
                clip_on=False,
            )
        )
        fig.text(x + 0.026, 0.104, name, color=INK, fontsize=11, va="center", ha="left")
        fig.text(
            x + 0.026,
            0.073,
            f"{n:,} posts  ·  {pct}",
            color=SOFT,
            fontsize=9.5,
            va="center",
            ha="left",
        )

    fig.text(
        0.055,
        0.028,
        "A naive map plots only the 80 maroon squares (1.6%). "
        "Place-resolution recovers the 720 steel squares, reaching 16% mappable;",
        color=FAINT,
        fontsize=9,
        ha="left",
        va="bottom",
    )
    fig.text(
        0.055,
        0.008,
        "the 4,200 grey squares carry no location, and coverage() "
        "reports them instead of dropping them.",
        color=FAINT,
        fontsize=9,
        ha="left",
        va="bottom",
    )

    fig.savefig(out_dir / "geosocialx-coverage.png", dpi=220, facecolor=PAPER)
    plt.close(fig)

    # ====================================================================
    # figure 2 : two-panel San Francisco map
    # ====================================================================
    outline = [
        (-122.5045, 37.7080),
        (-122.5090, 37.7250),
        (-122.5110, 37.7520),
        (-122.5100, 37.7710),
        (-122.5130, 37.7800),
        (-122.5085, 37.7875),
        (-122.4945, 37.7885),
        (-122.4790, 37.8110),
        (-122.4720, 37.8092),
        (-122.4660, 37.8100),
        (-122.4480, 37.8086),
        (-122.4360, 37.8082),
        (-122.4230, 37.8088),
        (-122.4130, 37.8086),
        (-122.4030, 37.8082),
        (-122.3945, 37.8076),
        (-122.3855, 37.8080),
        (-122.3820, 37.7965),
        (-122.3865, 37.7900),
        (-122.3878, 37.7820),
        (-122.3860, 37.7720),
        (-122.3862, 37.7620),
        (-122.3800, 37.7520),
        (-122.3768, 37.7380),
        (-122.3782, 37.7280),
        (-122.3835, 37.7200),
        (-122.3880, 37.7120),
        (-122.4055, 37.7082),
        (-122.4320, 37.7085),
        (-122.4720, 37.7080),
    ]
    extent = (-122.527, -122.363, 37.700, 37.822)
    key = {
        "Mission": (0.0, -0.005, "center", "top"),
        "SoMa": (0.005, 0.001, "left", "center"),
        "Financial District": (0.004, 0.003, "left", "bottom"),
        "Marina": (0.0, 0.004, "center", "bottom"),
        "Castro": (-0.005, -0.002, "right", "top"),
        "Sunset": (0.0, -0.005, "center", "top"),
        "Richmond": (0.0, 0.005, "center", "bottom"),
    }

    def basemap(ax):
        ax.add_patch(
            MplPolygon(
                outline,
                closed=True,
                facecolor=LAND,
                edgecolor=RULE,
                linewidth=1.2,
                joinstyle="round",
                zorder=0,
            )
        )
        for name in key:
            lon, lat = HOODS[name]
            ax.plot(lon, lat, "o", ms=2.2, color=FAINT, alpha=0.6, zorder=1)
        for name, (dx, dy, ha, va) in key.items():
            lon, lat = HOODS[name]
            ax.text(
                lon + dx,
                lat + dy,
                name,
                fontsize=6.2,
                color=SOFT,
                ha=ha,
                va=va,
                zorder=6,
            )
        ax.text(
            -122.519,
            37.735,
            "PACIFIC\nOCEAN",
            fontsize=6.5,
            color=WATER,
            ha="center",
            va="center",
            style="italic",
            linespacing=1.3,
            zorder=1,
        )
        ax.text(
            -122.368,
            37.812,
            "SAN\nFRANCISCO\nBAY",
            fontsize=6,
            color=WATER,
            ha="right",
            va="top",
            style="italic",
            linespacing=1.3,
            zorder=1,
        )
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_aspect(1.0 / np.cos(np.radians(37.76)))
        for s in ax.spines.values():
            s.set_color(RULE)
            s.set_linewidth(1.0)
        ax.set_xticks([])
        ax.set_yticks([])
        dlon = 2.0 / (111.32 * np.cos(np.radians(37.76)))
        x0, y0 = -122.523, 37.706
        ax.plot(
            [x0, x0 + dlon],
            [y0, y0],
            color=INK,
            lw=2.6,
            solid_capstyle="butt",
            zorder=7,
        )
        ax.text(
            x0 + dlon / 2,
            y0 + 0.0024,
            "2 km",
            ha="center",
            va="bottom",
            color=SOFT,
            fontsize=6.8,
            zorder=7,
        )
        nx = -122.516
        ax.annotate(
            "",
            xy=(nx, 37.816),
            xytext=(nx, 37.803),
            zorder=7,
            arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.1),
        )
        ax.text(
            nx,
            37.819,
            "N",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold",
            color=INK,
            zorder=7,
        )

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.4, 5.1))
    fig.patch.set_facecolor(PAPER)
    for ax in (axL, axR):
        ax.set_facecolor(PAPER)
        basemap(ax)

    xs = [p.longitude for p in naive]
    ys = [p.latitude for p in naive]
    counts = Counter(
        (round(p.longitude, 4), round(p.latitude, 4))
        for p in honest
        if p.source == "place"
    )

    axL.scatter(
        xs, ys, s=15, color=MAROON, alpha=0.9, edgecolor=PAPER, linewidth=0.4, zorder=5
    )
    for (lon, lat), c in counts.items():
        axR.scatter(
            lon,
            lat,
            s=16 * np.sqrt(c),
            facecolor="none",
            edgecolor=STEEL,
            linewidth=1.5,
            alpha=0.9,
            zorder=4,
        )
    axR.scatter(
        xs, ys, s=15, color=MAROON, alpha=0.9, edgecolor=PAPER, linewidth=0.4, zorder=5
    )

    for ax, tag, sub in (
        (axL, "(a)  exact coordinates only", "80 points  ·  1.6% of the corpus"),
        (axR, "(b)  with place-resolution", "800 points  ·  16%  ·  10x more"),
    ):
        ax.text(
            0.0,
            1.055,
            tag,
            transform=ax.transAxes,
            fontsize=10.5,
            fontweight="bold",
            color=INK,
            ha="left",
            va="bottom",
            clip_on=False,
        )
        ax.text(
            0.0,
            1.012,
            sub,
            transform=ax.transAxes,
            fontsize=8.5,
            color=SOFT,
            ha="left",
            va="bottom",
            clip_on=False,
        )

    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor=MAROON,
            markeredgecolor=PAPER,
            markersize=7,
            label="exact coordinate (one post)",
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor="none",
            markeredgecolor=STEEL,
            markersize=11,
            markeredgewidth=1.5,
            label="place centroid (bigger ring = more posts)",
        ),
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=9,
        bbox_to_anchor=(0.5, 0.0),
        labelcolor=SOFT,
    )

    fig.suptitle(
        "Same 5,000 posts, mapped two ways",
        color=INK,
        fontsize=14,
        fontweight="bold",
        x=0.03,
        ha="left",
        y=0.99,
    )
    fig.text(
        0.03,
        0.928,
        "The honest map is ten times fuller but coarser, "
        "snapped to neighbourhood centroids.",
        color=SOFT,
        fontsize=10,
        ha="left",
    )
    fig.subplots_adjust(left=0.02, right=0.98, top=0.80, bottom=0.09, wspace=0.06)

    fig.savefig(out_dir / "geosocialx-maps.png", dpi=220, facecolor=PAPER)
    plt.close(fig)
    print(f"\nwrote geosocialx-coverage.png and geosocialx-maps.png to {out_dir}")


if __name__ == "__main__":
    main()
