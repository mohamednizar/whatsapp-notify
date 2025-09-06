from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_digital_product = fields.Boolean(
        string='Is Digital Product',
        default=False,
        help='Check if this product is a digital product (e-book, software, etc.)'
    )
    
    digital_download_link = fields.Char(
        string='Download Link',
        help='Direct download link for the digital product'
    )
    
    digital_download_links = fields.Text(
        string='Download Links',
        help='Multiple download links (JSON format) for digital products'
    )

    def _validate_digital_product_schema(self):
        """Validate if product is a digital product and has valid download links"""
        self.ensure_one()
        
        result = {
            'is_valid': False,
            'download_links': [],
            'errors': []
        }
        
        if not self.is_digital_product:
            result['errors'].append('Product is not marked as digital product')
            return result
        
        # Check for download links
        download_links = []
        
        # First check single download link
        if self.digital_download_link:
            download_links.append(self.digital_download_link)
        
        # Then check multiple download links (JSON format)
        if self.digital_download_links:
            try:
                import json
                links_data = json.loads(self.digital_download_links)
                if isinstance(links_data, list):
                    download_links.extend(links_data)
                elif isinstance(links_data, str):
                    download_links.append(links_data)
            except (json.JSONDecodeError, TypeError):
                # If JSON parsing fails, treat as single string
                download_links.append(self.digital_download_links)
        
        if not download_links:
            result['errors'].append('No download links found for digital product')
            return result
        
        # Validate links (basic validation)
        valid_links = []
        for link in download_links:
            if link and isinstance(link, str) and (link.startswith('http://') or link.startswith('https://')):
                valid_links.append(link)
            else:
                result['errors'].append(f'Invalid download link: {link}')
        
        if valid_links:
            result['is_valid'] = True
            result['download_links'] = valid_links
        
        return result


class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    def _validate_digital_product_schema(self):
        """Validate if product is a digital product and has valid download links"""
        # Delegate to product template
        return self.product_tmpl_id._validate_digital_product_schema()