# WhatsApp Notify Models

from . import whatsapp_config
from . import whatsapp_message
from . import whatsapp_template
from . import res_partner
from . import product_template

# Conditionally import POS integration if POS module is available
try:
    from . import pos_order
except ImportError:
    # POS module not available, skip POS integration
    pass
