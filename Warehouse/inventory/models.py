import datetime
from django.db import models

# Create your models here.
class Item(models.Model):
    """
    物料
    """
    itemname = models.CharField(max_length=50)  # 物料名称
    itemsize = models.CharField(max_length=50)  # 物料规格
    producer = models.CharField(max_length=50)  # 生产厂家
    supplier = models.CharField(max_length=50)  # 供应商
    price = models.DecimalField(max_digits=14, decimal_places=2)  # 单价
    remark = models.CharField(max_length=200, blank=True)  # 备注

    def __str__(self):
        return self.itemname

    class Meta:
        verbose_name = 'name'
        verbose_name_plural = 'name'


class Inventory(models.Model):
    """
    库存信息
    """
    STATUS = (
        ('0', "工具"),
        ('1', "辅料"),
        ('2', "备件")
    )
    item = models.ForeignKey(Item,verbose_name='item')
    count = models.DecimalField(max_digits=14,decimal_places=2)
    location = models.CharField(max_length=50,blank=True,null=True)
    maxcnt = models.DecimalField(max_digits=14,decimal_places=2)  # 最高库存
    mincnt = models.DecimalField(max_digits=14,decimal_places=2)  # 最低库存
    classify = models.SmallIntegerField(choices=STATUS, verbose_name='分类')

    def __str__(self):
        return self.item

    # class Meta:
    #     verbose_name = _("Inventory")
    #     verbose_name_plural = _("Inventory")
    #     ordering = ['material']


class StockIn(models.Model):
    """
    入库单
    """
    # STATUS = (
    #     ('0', "NEW"),
    #     ('1', "QUALITY TESTING"),
    #     ('9', "EXECUTED")
    # )
    # index_weight = 3
    code = models.CharField("code",max_length=20,blank=True,null=True)
    item = models.ForeignKey(Item,verbose_name="item")
    # user = models.ForeignKey(User,verbose_name="user",blank=True,null=True)
    operator = models.CharField(max_length=40)
    # status = models.CharField(_("status"),max_length=const.DB_CHAR_CODE_2,default='0',choices=STATUS)
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
        if self.initem_set.count() > 0:
            with transaction.atomic():
                total_amount = decimal.Decimal(0)
                for item in self.initem_set.filter(status=0).all():
                    try:
                        inventory = Inventory.objects.get(warehouse=self.warehouse,material=item.material,measure=item.measure)
                        if inventory.price != item.price:
                            at = decimal.Decimal(inventory.price*inventory.cnt+item.price*item.cnt)
                            ac = decimal.Decimal(inventory.cnt+item.cnt)
                            average = at/ac
                            inventory.price = average
                            item.material.stock_price = average
                            item.material.save()
                        inventory.cnt += item.cnt
                        inventory.save()
                        total_amount += item.price*item.cnt
                    except Exception,e:
                        Inventory.objects.create(warehouse=self.warehouse,material=item.material,measure=item.measure,
                                                 cnt=item.cnt,price=item.price,org=self.org)
                        item.material.stock_price = item.price
                        item.material.save()

                        item.status=1
                        item.event_time = datetime.datetime.now()
                        item.source = self.code
                        item.save()
                        total_amount += item.price*item.cnt
                    # saving the purchase item
                    item.po_item.is_in_stock = 1
                    item.po_item.in_stock_time = datetime.datetime.now()
                    item.po_item.entry_cnt = item.cnt

                    item.po_item.save()
                    none_zero_left = POItem.objects.filter(po=item.po_item.po,left_cnt__gt=0).count()
                    if none_zero_left == 0:
                        item.po_item.po.status = '99'
                        item.po_item.po.entry_status = 1
                        item.po_item.po.entry_time = datetime.datetime.now()
                        item.po_item.po.save()
                    # saving stock in item status
                    item.status = 1
                    item.event_time = datetime.datetime.now()
                # updating master's record
                self.status = 9
                self.execute_time = datetime.datetime.now()
                self.amount = total_amount
                self.save()

    class Meta:
        verbose_name = "StockIn"
        verbose_name_plural = "StockIn"


class StockOut(generic.BO):
    """
    领料单
    """
    STATUS = (
        ('0', _("NEW")),
        ('1', _("IN PROGRESS")),
        ('9', _("EXECUTED"))
    )
    index_weight = 2
    code = models.CharField(_("code"),max_length=const.DB_CHAR_NAME_20,blank=True,null=True)
    org = models.ForeignKey(Organization,verbose_name=_("organization"),blank=True,null=True)
    title = models.CharField(_("title"),max_length=const.DB_CHAR_NAME_40)
    project = models.ForeignKey(Project,verbose_name=_("project"),blank=True,null=True)
    wo = models.ForeignKey(WorkOrder,verbose_name=_("work order"),blank=True,null=True)
    description = models.TextField(_("description"),blank=True,null=True)
    amount = models.DecimalField(_("money of amount"),max_digits=14,decimal_places=4,blank=True,null=True)
    user = models.ForeignKey(User,verbose_name=_("out user"),blank=True,null=True)
    status = models.CharField(_("status"),max_length=const.DB_CHAR_CODE_2,default='0',choices=STATUS)
    execute_time = models.DateTimeField(_("execute time"),blank=True,null=True)

    def out_amount(self):
        return self.amount or ''

    def out_time(self):
        return self.execute_time or ''

    out_time.short_description = _('stock out time')
    out_amount.short_description = _('stock out amount')

    def action_out(self,request=None):
        """
        执行出库操作
        """
        if self.outitem_set.count() > 0:
            with transaction.atomic():
                total = decimal.Decimal(0)
                for item in OutItem.objects.filter(master=self).all():
                    if item.inventory.cnt < item.cnt:
                        raise Exception('%s does not meets required' % item.material)
                    if item.cnt:
                        total += item.cnt * item.inventory.price
                        item.inventory.cnt -= item.cnt
                        item.status = 1
                        item.price = item.inventory.price
                        item.event_time = datetime.datetime.now()
                        item.inventory.save()
                        item.source=self.code
                        item.save()
                if total > 0:
                    self.amount = total
                self.status = '9'
                self.execute_time = datetime.datetime.now()
                self.save()

    class Meta:
        verbose_name = _("StockOut")
        verbose_name_plural = _("StockOut")


class WareReturn(generic.BO):
    """
    返库单
    """
    STATUS = (
        ('0', _("NEW")),
        ('1', _("IN PROGRESS")),
        ('9', _("EXECUTED"))
    )
    index_weight = 5
    code = models.CharField(_("code"),max_length=const.DB_CHAR_NAME_20,blank=True,null=True)
    org = models.ForeignKey(Organization,verbose_name=_("organization"),blank=True,null=True)
    title = models.CharField(_("title"),max_length=const.DB_CHAR_NAME_40)
    out = models.ForeignKey(StockOut,verbose_name=_('StockOut'))
    amount = models.DecimalField(_("money of amount"),max_digits=14,decimal_places=4,blank=True,null=True)
    user = models.ForeignKey(User,verbose_name=_("out user"),blank=True,null=True)
    status = models.CharField(_("status"),max_length=const.DB_CHAR_CODE_2,default='0',choices=STATUS)
    execute_time = models.DateTimeField(_("execute time"),blank=True,null=True)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(WareReturn,self).save(force_insert,force_update,using,update_fields)
        item_count = ReturnItem.objects.filter(master=self).count()
        if self.out and item_count == 0:
            for out_item in OutItem.objects.filter(master=self.out):
                ReturnItem.objects.create(master=self,out_item=out_item,material=out_item.material,price=out_item.price,
                                          measure=out_item.measure,warehouse=out_item.warehouse,out_cnt=out_item.cnt,cnt=out_item.cnt)

    def action_return(self,request):
        with transaction.atomic():
            total_amount = decimal.Decimal(0)
            for item in ReturnItem.objects.filter(master=self):
                if item.cnt > item.out_item.cnt or item.cnt < 0:
                    raise Exception('%s cnt is invalid,out is %s,return is %s' % (item.material,item.out_cnt,item.cnt))
                item.event_time = datetime.datetime.now()
                item.source = self.code
                item.status = 1
                item.out_item.inventory.cnt += item.cnt
                item.out_item.inventory.save()
                item.save()
                total_amount += item.price * item.cnt
            self.amount = total_amount
            self.status = '9'
            self.execute_time = datetime.datetime.now()
            self.save()

    class Meta:
        verbose_name = _("ware return")
        verbose_name_plural = _("ware return")
