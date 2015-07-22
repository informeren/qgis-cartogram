"""Plugin entry point."""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load Cartogram class from file cartogram."""
    from .cartogram import Cartogram
    return Cartogram(iface)
