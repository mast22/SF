import io
import segno
from qr_code.qrcode.utils import QRCodeOptions
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.renderers import BaseRenderer


class BrowsableAPIRendererWithoutForms(BrowsableAPIRenderer):
    """Renders the browsable api, but excludes the forms."""
    format = 'api-without-forms'

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        ctx["display_edit_forms"] = False
        return ctx

    def show_form_for_method(self, view, method, request, obj):
        """We never want to do this! So just return False."""
        return False

    def get_rendered_html_form(self, data, view, method, request):
        """Why render _any_ forms at all. This method should return
        rendered HTML, so let's simply return an empty string.
        """
        return ''


class BrowsableAPIRendererWithoutPostForm(BrowsableAPIRenderer):
    """Renders the browsable api, but excludes the forms."""
    format = 'api-without-post-forms'

    def get_context(self, *args, **kwargs):
        ctx = super().get_context(*args, **kwargs)
        # ctx["display_edit_forms"] = False
        return ctx

    def show_form_for_method(self, view, method, request, obj):
        """We never want to do this! So just return False."""
        return False if method == 'POST' else True

    def get_rendered_html_form(self, data, view, method, request):
        """Why render _any_ forms at all. This method should return
        rendered HTML, so let's simply return an empty string.
        """
        if method in ('POST', 'PUT'):
            return ''
        else:
            return super().get_rendered_html_form(data, view, method, request)



class BaseQRCodeURLRenderer(BaseRenderer):
    media_type = None
    format = 'qrcode'
    charset = None
    render_style = 'binary'
    url_key = 'url'
    default_options = {
        'image_format': None
    }
    image_format = None

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into QR-Code, returning a bytestring.
        """
        if data is None:
            return b''

        if isinstance(data, dict) and self.url_key in data:
            data = data['url']
        qr_code_options = QRCodeOptions(**{
            **self.default_options,
            **renderer_context.get('options', {})
        })
        qr_code = segno.make(str(data), **qr_code_options.kw_make())
        out = io.BytesIO()
        qr_code.save(out, **qr_code_options.kw_save())
        return out.getvalue()


class QRCodeSVGRenderer(BaseQRCodeURLRenderer):
    media_type = 'image/svg+xml'
    format = 'qrcode-svg'
    default_options = {**BaseQRCodeURLRenderer.default_options, **{
        'image_format': 'svg'
    }}


class QRCodePNGRenderer(BaseQRCodeURLRenderer):
    media_type = 'image/png'
    format = 'qrcode-png'
    default_options = {**BaseQRCodeURLRenderer.default_options, **{
        'image_format': 'png'
    }}

