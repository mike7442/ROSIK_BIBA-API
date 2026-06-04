import struct

float_number = 3942594.0
bytes_float = struct.pack('<f', float_number)
print(bytes_float)  # Output: b'\xdb\x0fI@'
print(len(bytes_float))