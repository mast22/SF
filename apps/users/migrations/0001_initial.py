# Generated by Django 3.2.6 on 2021-08-27 12:48

import apps.users.models.user
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import netfields.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('partners', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, region=None, unique=True, verbose_name='Номер телефона')),
                ('first_name', models.CharField(max_length=100, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=100, verbose_name='Фамилия')),
                ('middle_name', models.CharField(max_length=100, null=True, verbose_name='Отчество')),
                ('email', models.EmailField(max_length=254, null=True, unique=True, verbose_name='Email')),
                ('status', models.CharField(choices=[('active', 'Активен'), ('blocked', 'Заблокирован'), ('removed', 'Удалён')], default='active', max_length=20, verbose_name='Статус')),
                ('role', models.CharField(choices=[('admin', 'Администратор'), ('acc_man', 'Аккаунт-мереджер'), ('ter_man', 'Территориальный-менеджер'), ('agent', 'Агент')], max_length=7, verbose_name='Роль')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='superuser status')),
                ('telegram_id', models.CharField(default=None, max_length=9, null=True, verbose_name='ID телеграмма')),
                ('can_edit_bank_priority', models.BooleanField(default=None, null=True, verbose_name='Может редактировать приоритет банков')),
                ('region', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='ter_mans', to='partners.region')),
            ],
            managers=[
                ('objects', apps.users.models.user.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(blank=True, max_length=256, primary_key=True, serialize=False, verbose_name='Токен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Момент создания')),
                ('moment_end', models.DateTimeField(blank=True, verbose_name='Момент завершения')),
                ('type', models.CharField(choices=[('access', 'Токен доступа'), ('refresh', 'Токен обновления')], default='access', max_length=10, verbose_name='Тип')),
                ('parent', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.token')),
                ('user', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Токен',
                'verbose_name_plural': 'Токены',
                'permissions': (),
            },
        ),
        migrations.CreateModel(
            name='TempToken',
            fields=[
                ('key', models.CharField(blank=True, max_length=256, primary_key=True, serialize=False, verbose_name='Токен')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Момент создания')),
                ('moment_end', models.DateTimeField(blank=True, verbose_name='Момент завершения')),
                ('type', models.CharField(choices=[('login-confirm', 'Подтверждение при входе'), ('passwd-reset', 'Сброс пароля'), ('passwd-confirm', 'Подтверждение пароля'), ('new-client', 'Добавление клиента')], default='passwd-reset', max_length=14, verbose_name='Тип')),
                ('phone', models.CharField(max_length=14, null=True, verbose_name='Номер телефона')),
                ('code', models.CharField(max_length=10, null=True, verbose_name='Проверочный код')),
                ('provider_uuid', models.CharField(blank=True, default='', max_length=200, null=True, verbose_name='Provider UUID')),
                ('send_type', models.CharField(choices=[('sms', 'SMS-сообщение'), ('email', 'Email-сообщение'), ('push', 'Push-сообщение'), ('voice-message', 'Аудио-сообщение'), ('dialing', 'Дозвон'), ('telegram', 'Сообщение в Telegram')], default='sms', max_length=15, verbose_name='Способ отправки')),
                ('send_status', models.CharField(choices=[('no-sent', 'Не отправлено'), ('sent', 'Отправлено'), ('received', 'Получено'), ('error', 'Ошибка')], default='no-sent', max_length=10, verbose_name='Status')),
                ('received_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата получения')),
                ('can_repeat_at', models.DateTimeField(blank=True, help_text='Момент времени, после которого возможна повторная отправка', verbose_name='Дата повтора')),
                ('expires_at', models.DateTimeField(blank=True, help_text='Момент времени, после которого токен становится не действительным', verbose_name='Дата истечения')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Временный токен',
                'verbose_name_plural': 'Временные токены',
                'permissions': (),
            },
        ),
        migrations.CreateModel(
            name='AccMan',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('users.user',),
            managers=[
                ('objects', apps.users.models.user.AccManManager()),
            ],
        ),
        migrations.CreateModel(
            name='Admin',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('users.user',),
            managers=[
                ('objects', apps.users.models.user.AdminManager()),
            ],
        ),
        migrations.CreateModel(
            name='Agent',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('users.user',),
            managers=[
                ('objects', apps.users.models.user.AgentManager()),
            ],
        ),
        migrations.CreateModel(
            name='TerMan',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('users.user',),
            managers=[
                ('objects', apps.users.models.user.TerManManger()),
            ],
        ),
        migrations.CreateModel(
            name='AllowedIP',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('ip', netfields.fields.InetAddressField(max_length=39, verbose_name='IP-адрес')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allowed_ips', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Разрешённый IP-адрес',
                'verbose_name_plural': 'Разрешённые IP-адреса',
                'unique_together': {('ip', 'user')},
            },
        ),
        migrations.AddField(
            model_name='user',
            name='ter_man',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='agents', to='users.terman'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('region__isnull', False), ('role', 'ter_man')), models.Q(('region__isnull', True), ('role__in', ['agent', 'admin', 'acc_man'])), _connector='OR')), name='user_region_constraint'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('role', 'agent'), ('ter_man__isnull', False)), models.Q(('role__in', ['admin', 'acc_man', 'ter_man']), ('ter_man__isnull', True)), _connector='OR')), name='user_ter_man_constraint'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('can_edit_bank_priority__isnull', False), ('role__in', ['ter_man'])), models.Q(('can_edit_bank_priority__isnull', True), ('role__in', ['admin', 'acc_man', 'agent'])), _connector='OR')), name='user_can_edit_bank_priority_constraint'),
        ),
    ]