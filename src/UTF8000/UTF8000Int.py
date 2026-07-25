from .UTF8000Byte import UTF8000Byte

class UTF8000Int:
    def __init__(self, utf_8000_bytes: list[UTF8000Byte]) -> None:
        # No validation is done; we're assuming these come from `UTF8000IncrementalDecoder`
        self.utf_8000_bytes = utf_8000_bytes

    def __str__(self) -> str:
        return " ".join(str(b) for b in self.utf_8000_bytes)

    def __int__(self) -> int:
        ret = 0
        content_bytes = (b for b in self.utf_8000_bytes if b.is_content_byte)
        for content_byte in content_bytes:
            ret <<= content_byte.n_bits_content_total
            ret += content_byte.content
        return ret

    @property
    def n_bytes(self) -> int:
        return len(self.utf_8000_bytes)

    @property
    def n_bits_content_total(self) -> int:
        """
        The number of content bits that the code unit contains.

        This is the 'capacity' of the code unit, not the count of 'occupied' bits.
        """
        return sum(b.n_bits_content_total for b in self.utf_8000_bytes)

    @property
    def n_bits_content_mandatory(self) -> int:
        """
        The number of mandatory content bits that the code unit contains.

        This is the 'capacity' of the code unit, not the count of 'occupied' bits.
        """
        return sum(b.n_bits_content_mandatory for b in self.utf_8000_bytes)
