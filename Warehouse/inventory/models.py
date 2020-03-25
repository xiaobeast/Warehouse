import datetime
import decimal
from django.db import models

# Create your models here.
class Item(models.Model):
    """
    物料
    """
    STATUS = (
        ('0', "工具"),
        ('1', "辅料"),
        ('2', "备件"),
    )
    item = models.CharField(max_length=50, verbose_name='物料名称')  # 物料名称
    itemsize = models.CharField(max_length=50, verbose_name='规格型号')  # 物料规格
    count = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='库存数量')
    producer = models.CharField(max_length=50, verbose_name='生产厂家')  # 生产厂家
    supplier = models.CharField(max_length=50, verbose_name='供应商')  # 供应商
    price = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='单价')  # 单价
    location = models.CharField(max_length=50, blank=True, null=True, verbose_name='库位号')
    maxcnt = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='最高库存')  # 最高库存
    mincnt = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='最低库存')  # 最低库存
    classify = models.CharField(choices=STATUS, max_length=20, verbose_name='分类')
    remark = models.CharField(max_length=200, blank=True, verbose_name='备注')  # 备注

    def __str__(self):
        return self.item

    class Meta:
        verbose_name = 'item'
        verbose_name_plural = 'item'


# class Inventory(models.Model):
#     """
#     库存信息
#     """
#     STATUS = (
#         ('0', "工具"),
#         ('1', "辅料"),
#         ('2', "备件"),
#     )
#     item = models.OneToOneField(Item,verbose_name='item')
#     count = models.DecimalField(max_digits=14,decimal_places=2, verbose_name='库存数量')
#     location = models.CharField(max_length=50,blank=True,null=True, verbose_name='库位号')
#     maxcnt = models.DecimalField(max_digits=14,decimal_places=2, verbose_name='最高库存')  # 最高库存
#     mincnt = models.DecimalField(max_digits=14,decimal_places=2, verbose_name='最低库存')  # 最低库存
#     classify = models.CharField(choices=STATUS, max_length=20, verbose_name='分类')
#
#     def __str__(self):
#         return self.item.item
#
#     class Meta:
#         verbose_name = "Inventory"
#         verbose_name_plural = "Inventory"
#         ordering = ['location']


class StockIn(models.Model):
    """
    入库单
    """
    code = models.CharField("code",max_length=20,blank=True,null=True)
    item = models.ForeignKey(Item,verbose_name="item")
    operator = models.CharField(max_length=40)
    execute_time = models.DateTimeField("execute time",blank=True,null=True)
    amount = models.IntegerField(null=True)

    def money_of_amount(self):
        if self.amount:
            return self.amount
        else:
            return 0.00

    def entry_time(self):
        if self.execute_time:
            return self.execute_time
        else:
            return ''

    money_of_amount.short_description = "stock in money of amount"
    entry_time.short_description = "entry time"

    def action_entry(self,request):
        """
        执行入库操作
        """
        pass

    class Meta:
        verbose_name = "StockIn"
        verbose_name_plural = "StockIn"


class StockOut(models.Model):
    """
    领料单
    """
    code = models.CharField("code", max_length=20, blank=True, null=True)
    item = models.ForeignKey(Item, verbose_name="item")
    operator = models.CharField(max_length=40)
    execute_time = models.DateTimeField("execute time", blank=True, null=True)
    amount = models.IntegerField(null=True)

    def out_amount(self):
        return self.amount or ''

    def out_time(self):
        return self.execute_time or ''

    out_time.short_description = 'stock out time'
    out_amount.short_description = 'stock out amount'

    def action_out(self,request=None):
        """
        执行出库操作
        """
        pass

    class Meta:
        verbose_name = "StockOut"
        verbose_name_plural = "StockOut"


class ItemReturn(models.Model):
    """
    返库单
    """
    code = models.CharField("code", max_length=20, blank=True, null=True)
    item = models.ForeignKey(Item, verbose_name="item")
    operator = models.CharField(max_length=40)
    execute_time = models.DateTimeField("execute time", blank=True, null=True)
    amount = models.IntegerField(null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        pass

    def action_return(self,request):
        pass

    class Meta:
        verbose_name = "ware return"
        verbose_name_plural = "ware return"