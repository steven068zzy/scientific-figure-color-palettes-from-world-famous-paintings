"""masterpalettes — scientific color palettes extracted from 100 masterpiece paintings.

Quick start::

    import masterpalettes as mp

    mp.list_palettes()               # all 100 palette names
    mp.colors("starry_night")        # 8 hex colors, data-ready order
    mp.roles("starry_night")         # role -> hex list (primary/secondary/accent/...)
    mp.cmap("starry_night")          # diverging matplotlib colormap
    mp.apply("starry_night")         # set matplotlib prop_cycle to this palette
    mp.register_matplotlib()         # register all cmaps as "mp.<name>"
"""
import json
import os
from functools import lru_cache

__version__ = "1.0.0"
__all__ = ["list_palettes", "get_palette", "colors", "color_names", "roles",
           "diverging", "cmap", "cycler", "apply", "register_matplotlib"]

_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "palettes.json")


@lru_cache(maxsize=1)
def _data():
    with open(_DATA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def list_palettes():
    """All palette names, in collection order."""
    return list(_data().keys())


def get_palette(name):
    """Full palette record: painting metadata, named colors, roles, diverging stops."""
    try:
        return _data()[name]
    except KeyError:
        raise KeyError(f"unknown palette {name!r}; see list_palettes()") from None


def colors(name, n=None):
    """Hex colors in data-plotting order (warm pair, cool pair, dark, supports, light)."""
    cs = [c[1] for c in get_palette(name)["colors"]]
    return cs if n is None else cs[:n]


def color_names(name):
    """Evocative color names, aligned with colors()."""
    return [c[0] for c in get_palette(name)["colors"]]


def roles(name):
    """Role assignments: Primary Data (Warm), Secondary Data (Cool), Tertiary / Support,
    Highlight / Accent, Backgrounds, Text / Lines."""
    return get_palette(name)["roles"]


def diverging(name):
    """Three diverging stops [cold, neutral light, warm accent]."""
    return get_palette(name)["diverging"]


def cmap(name, kind="diverging", n=256):
    """Matplotlib colormap. kind='diverging' (continuous, for heatmaps/surfaces)
    or kind='listed' (categorical)."""
    from matplotlib.colors import LinearSegmentedColormap, ListedColormap
    if kind == "diverging":
        return LinearSegmentedColormap.from_list(f"mp.{name}", diverging(name), N=n)
    return ListedColormap(colors(name), name=f"mp.{name}_listed")


def cycler(name, n=6):
    """A matplotlib cycler over the first n data colors."""
    from cycler import cycler as _cycler
    return _cycler(color=colors(name, n))


def apply(name, n=6):
    """Set matplotlib's default color cycle to this palette."""
    import matplotlib as mpl
    mpl.rcParams["axes.prop_cycle"] = cycler(name, n)


def register_matplotlib():
    """Register every palette as matplotlib colormaps: 'mp.<name>' (diverging)
    and 'mp.<name>_listed' (categorical). Then use e.g. cmap='mp.starry_night'."""
    import matplotlib as mpl
    for name in list_palettes():
        for kind, suffix in (("diverging", ""), ("listed", "_listed")):
            cm = cmap(name, kind=kind)
            try:
                mpl.colormaps.register(cm, name=f"mp.{name}{suffix}", force=True)
            except AttributeError:  # matplotlib < 3.5
                mpl.cm.register_cmap(name=f"mp.{name}{suffix}", cmap=cm)
