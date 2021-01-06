from string import ascii_letters, printable
from typing import Generator, Dict, Any

from hypothesis import given, settings, strategies as st


def generate_session_data() -> Dict[str, Any]:
    """Factory method for generating mocked session data."""
    return st.dictionaries(
        st.text(ascii_letters, min_size=5, max_size=20),
        st.recursive(
            st.floats()
            | st.integers()
            | st.text(printable)
            | st.booleans()
            | st.nothing()
            | st.timedeltas()
            | st.times()
            | st.uuids(),
            st.lists,
        ),
        min_size=5,
        max_size=10,
    ).example()