import usb_cdc
import storage

# Remove the filesystem
# storage.disable_usb_drive()

# Data Serial
usb_cdc.enable(console=True, data=True)
