# Generated by Django 2.2.13 on 2020-07-28 13:28

from django.db import migrations, models
import django.db.models.deletion
import snippets.base.fields


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0038_auto_20200624_1213'),
    ]

    operations = [
        migrations.CreateModel(
            name='SendToDeviceSingleSceneTemplate',
            fields=[
                ('template_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='base.Template')),
                ('section_title_text', models.CharField(blank=True, help_text='Section title text. section_title_icon must also be specified to display.', max_length=255, verbose_name='Section Title Text')),
                ('section_title_url', snippets.base.fields.URLField(blank=True, help_text='A url, section_title_text links to this', max_length=500, verbose_name='Section Title URL')),
                ('text', models.TextField(help_text='Main text.', verbose_name='Text')),
                ('button_label', models.CharField(default='Send', help_text='Label for form submit button.', max_length=50, verbose_name='Button Label')),
                ('input_placeholder', models.CharField(default='Your email here', help_text='Placeholder text for email / phone number field.', max_length=255, verbose_name='Input Placeholder')),
                ('disclaimer_html', models.TextField(help_text='Text and link underneath the input box. HTML subset allowed: i, b, u, strong, em, br.', verbose_name='Disclaimer HTML')),
                ('locale', models.CharField(default='EN', help_text='Two to five character string for the locale code. Default "EN".', max_length=10)),
                ('country', models.CharField(default='us', help_text='Two character string for the country code (used for SMS). Default "us".', max_length=10)),
                ('include_sms', models.BooleanField(blank=True, default=False, help_text='Defines whether SMS is available.', verbose_name='Include SMS')),
                ('message_id_sms', models.CharField(blank=True, help_text='Newsletter/basket id representing the SMS message to be sent.', max_length=100, verbose_name='Message ID for SMS')),
                ('message_id_email', models.CharField(help_text='Newsletter/basket id representing the email message to be sent. Must be a value from the "Slug" column here: https://basket.mozilla.org/news/.', max_length=100, verbose_name='Message ID for Email')),
                ('success_title', models.TextField(help_text='Title of success message after form submission.', verbose_name='Success Title')),
                ('success_text', models.TextField(help_text='Text of success message after form submission.', verbose_name='Success Text')),
                ('error_text', models.TextField(help_text='Text of error message if form submission fails.', verbose_name='Error Text')),
                ('retry_button_label', models.CharField(default='Try again', help_text='Button label after a failed form submission', max_length=50, verbose_name='Retry Button Label')),
                ('block_button_text', models.CharField(default='Remove this', help_text='Tooltip text used for dismiss button.', max_length=50, verbose_name='Block Button Text')),
                ('do_not_autoblock', models.BooleanField(blank=True, default=False, help_text='Used to prevent blocking the snippet after the CTA (link or button) has been clicked.', verbose_name='Do Not Autoblock')),
                ('icon', models.ForeignKey(help_text='Image to display above the form. 192x192px PNG.', on_delete=django.db.models.deletion.PROTECT, related_name='sendtodevicesinglescene_icons', to='base.Icon', verbose_name='Icon')),
                ('section_title_icon', models.ForeignKey(blank=True, help_text='Section title icon. 64x64px. PNG. section_title_text must also be specified to display.', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sendtodevicesinglescene_section_icons', to='base.Icon', verbose_name='Section Title Icon')),
            ],
            bases=('base.template',),
        ),
    ]
