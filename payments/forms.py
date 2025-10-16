from django import forms

class PaymentForm(forms.Form):
    phone_number = forms.CharField(
        max_length=12,
        label="Phone Number",
        help_text="Mfano: 255620280809"
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        label="Amount (TZS)"
    )
