from pyluba.bluetooth import BleMessage

test = b'M\x04\x00\xdf\x08\xf8\x01\x10\x01\x18\x07 \x02(\x010\x018\x80\x80 B\xcb\x01b\xc8\x01\n\x12\x08\x01\x10\x06\x18\x01"\n1.10.5.237\n\x1e\x08\x01\x10\x03\x18\x01"\x161.6.22.2040 (3be066bf)\n\x1c\x08\x02\x10\x03\x18\x01"\x141.1.1.622 (a993d995)\n\x1b\x08\x03\x10\x03\x18\x01"\x132.2.0.150 (2cf62fc)\n\x1b\x08\x04\x10\x03\x18\x01"\x132.2.0.150 (2cf62fc)\n\x0c\x08\x05\x10\x03\x18\x01"\x047361\n\x1e\x08\x06\x10\x03\x18\x01"\x161.6.22.2040 (3be066bf)\n\x0c\x08\x07\x10\x03\x18\x01"\x041.28'

print(test.hex())
#
# message = BleMessage(None)
#
# message.parseNotification()