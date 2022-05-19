# Generated by Django 3.2.6 on 2021-08-27 12:48

from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        ('partners', '0001_initial'),
        ('banks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='termanbank',
            name='ter_man',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='terman_banks', to='users.terman'),
        ),
        migrations.AddField(
            model_name='outletextraservice',
            name='extra_service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outlet_extra_services', to='banks.extraservice'),
        ),
        migrations.AddField(
            model_name='outletextraservice',
            name='outlet_bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outlet_extra_services', to='banks.outletbank'),
        ),
        migrations.AddField(
            model_name='outletcreditproduct',
            name='credit_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outlet_credit_products', to='banks.creditproduct'),
        ),
        migrations.AddField(
            model_name='outletcreditproduct',
            name='outlet_bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outlet_credit_products', to='banks.outletbank'),
        ),
        migrations.AddField(
            model_name='outletbank',
            name='bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='outlet_banks', to='banks.bank'),
        ),
        migrations.AddField(
            model_name='outletbank',
            name='outlet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outlet_banks', to='partners.outlet'),
        ),
        migrations.AddField(
            model_name='extraservice',
            name='bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='extra_services', to='banks.bank'),
        ),
        migrations.AddField(
            model_name='creditproduct',
            name='bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='credit_products', to='banks.bank'),
        ),
        migrations.AddField(
            model_name='agentextraservice',
            name='agent_bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_extra_services', to='banks.agentbank'),
        ),
        migrations.AddField(
            model_name='agentextraservice',
            name='extra_service',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='agent_extra_services', to='banks.extraservice'),
        ),
        migrations.AddField(
            model_name='agentextraservice',
            name='terman_extra_service',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_extra_services', to='banks.termanextraservice'),
        ),
        migrations.AddField(
            model_name='agentcreditproduct',
            name='agent_bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_credit_products', to='banks.agentbank'),
        ),
        migrations.AddField(
            model_name='agentcreditproduct',
            name='credit_product',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='agent_credit_products', to='banks.creditproduct'),
        ),
        migrations.AddField(
            model_name='agentcreditproduct',
            name='terman_credit_product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_credit_products', to='banks.termancreditproduct'),
        ),
        migrations.AddField(
            model_name='agentbank',
            name='agent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_banks', to='users.agent'),
        ),
        migrations.AddField(
            model_name='agentbank',
            name='bank',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, related_name='agent_banks', to='banks.bank'),
        ),
        migrations.AddField(
            model_name='agentbank',
            name='terman_bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='agent_banks', to='banks.termanbank'),
        ),
        migrations.AddConstraint(
            model_name='termanextraservice',
            constraint=models.CheckConstraint(check=models.Q(('commission_min__lte', django.db.models.expressions.F('commission_max'))), name='terman_extra_services_commission_min_is_less_than_max'),
        ),
        migrations.AlterUniqueTogether(
            name='termanextraservice',
            unique_together={('terman_bank', 'extra_service')},
        ),
        migrations.AddConstraint(
            model_name='termancreditproduct',
            constraint=models.CheckConstraint(check=models.Q(('commission_min__lte', django.db.models.expressions.F('commission_max'))), name='terman_creditproducts_commission_min_is_less_than_max'),
        ),
        migrations.AlterUniqueTogether(
            name='termancreditproduct',
            unique_together={('terman_bank', 'credit_product')},
        ),
        migrations.AlterUniqueTogether(
            name='termanbank',
            unique_together={('bank', 'ter_man')},
        ),
        migrations.AlterUniqueTogether(
            name='outletextraservice',
            unique_together={('outlet_bank', 'extra_service')},
        ),
        migrations.AlterUniqueTogether(
            name='outletcreditproduct',
            unique_together={('outlet_bank', 'credit_product')},
        ),
        migrations.AlterUniqueTogether(
            name='outletbank',
            unique_together={('bank', 'outlet')},
        ),
        migrations.AlterUniqueTogether(
            name='agentextraservice',
            unique_together={('agent_bank', 'extra_service')},
        ),
        migrations.AlterUniqueTogether(
            name='agentcreditproduct',
            unique_together={('agent_bank', 'credit_product')},
        ),
        migrations.AlterUniqueTogether(
            name='agentbank',
            unique_together={('bank', 'agent')},
        ),
    ]