from django import forms
from user_side.models import User
import re

class SignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password',
        'class': 'form-control'
    }))
    
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Confirm Password',
        'class': 'form-control'
    }))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'mobile', 'password']

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs['placeholder'] = 'First name'
        self.fields['first_name'].widget.attrs['class'] = 'form-control' 

        self.fields['last_name'].widget.attrs['placeholder'] = 'Last name'
        self.fields['last_name'].widget.attrs['class'] = 'form-control' 

        self.fields['email'].widget.attrs['placeholder'] = 'Email'
        self.fields['email'].widget.attrs['class'] = 'form-control' 

        self.fields['mobile'].widget.attrs['placeholder'] = 'Mobile Number'
        self.fields['mobile'].widget.attrs['class'] = 'form-control' 


    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email.lower().endswith('@gmail.com'):
            raise forms.ValidationError("Please enter a valid Gmail address.")
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        mobile = ''.join(filter(str.isdigit, mobile))

        if len(mobile) != 10:
            raise forms.ValidationError("Mobile number must have exactly 10 digits.")

        if ' ' in mobile:
            raise forms.ValidationError("Mobile number cannot contain spaces.")

        if not re.match(r'^[789]\d{9}$', mobile):
            raise forms.ValidationError("Please enter a valid mobile number.")
        
        if re.match(r'^(\d)\1{9}$', mobile):
            raise forms.ValidationError("Please enter a valid mobile number.")

        return mobile
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if ' ' in password:
            raise forms.ValidationError("Password cannot contain spaces.")
        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        invalid_characters = [' ', '*', '#', '@', '$', '(', '+', '-', '!', '^', '&', ',','.']
        if any(char in first_name for char in invalid_characters):
            raise forms.ValidationError("First name cannot contain invalid characters.")
        if len(first_name) < 4:
            raise forms.ValidationError("First name is very short.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        invalid_characters = [' ', '*', '#', '@', '$', '(', '+', '-', '!', '^', '&', ',', '.']
        if any(char in last_name for char in invalid_characters):
            raise forms.ValidationError("Last name cannot contain invalid characters.")
        return last_name     

    def clean(self):
        cleaned_data = super(SignupForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')    

        if password != confirm_password:
            raise forms.ValidationError(
                "Password doesn't match"
            )

class CustomLoginForm(forms.Form):
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email'}),
        required=True
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}),
        required=True
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')

        if ' ' in password:
            raise forms.ValidationError("Password cannot contain spaces.")

        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password
    

class ChangePasswordForm(forms.Form):
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your new password'}),
        required=True
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        required=True
    )
    
    def clean_password(self):
        password = self.cleaned_data.get('password')

        if ' ' in password:
            raise forms.ValidationError("Password cannot contain empty spaces.")

        if len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long.")
        return password
    
    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')    

        if password != confirm_password:
            raise forms.ValidationError(
                "Password doesn't match"
            )

class ChangeCurrentPasswordForm(forms.Form):
    current_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Current password'}),
        required=True
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your new password'}),
        required=True
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        required=True
    )

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        user = self.user
        if not user.check_password(current_password):
            raise forms.ValidationError("Current password is incorrect")
        return current_password


class ProfileEditForm(forms.Form):

    first_name = forms.CharField(
        label='First name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your First name'}),
        required=True
    )
    last_name = forms.CharField(
        label='last_name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your new Last name'}),
        required=True
    )
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
        required=True
    )

    mobile = forms.CharField(
        label='Mobile',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile'}),
        required=True
    )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')

        invalid_characters = [' ', '*', '#','@','$','(','+','-','!','^','&',',','.']

        if any(char in first_name for char in invalid_characters):
            raise forms.ValidationError("First name cannot contain spaces and characters.")

        return first_name

    def clean_last_name(self):

        last_name = self.cleaned_data.get('last_name')

        invalid_characters = [' ', '*', '#','@','$','(','+','-','!','^','&',',','.']

        if any(char in last_name for char in invalid_characters):
            raise forms.ValidationError("Last name cannot contain spaces and special characters.")

        return last_name
    
    def clean_username(self):
        username = self.cleaned_data.get('username')

        invalid_characters = [' ', '*', '#','@','$','(','+','-','!','^','&',',','.']

        if any(char in username for char in invalid_characters):
            raise forms.ValidationError("Username can contain '_' and alphabets")


        return username

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        mobile = ''.join(filter(str.isdigit, mobile))

        if len(mobile) != 10:
            raise forms.ValidationError("Mobile number must have exactly 10 digits.")

        if ' ' in mobile:
            raise forms.ValidationError("Mobile number cannot contain spaces.")

        if not re.match(r'^[789]\d{9}$', mobile):
            raise forms.ValidationError("Please enter a valid mobile number.")
        
        if re.match(r'^(\d)\1{9}$', mobile):
            raise forms.ValidationError("Please enter a valid mobile number.")

        return mobile
    
    
