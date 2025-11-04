from apscheduler.schedulers.background import BackgroundScheduler
from django.db.models import Q
from django.conf import settings

from cmpapi.views import CmpRequestViewSet
from cmpapi.models import *
from cmpapi.serializers import *
from movierater.utils import *


# sched = BlockingScheduler()

def job_function():
    print('running job_function()')
    from datetime import datetime, timezone
    from datetime import date

    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    print(' Running on  %s' % (dt_string))

    compCode = settings.COMP_CODE
    msg = compCode + ' Done'

    # PDPA request on process report
    utils.sendMail_reminderRequestOnporcess(compCode)

    # PDPA Consent Dialy report
    utils.sendMail_ConsentDialy(compCode)

    # Wealth registration report
    utils.sendMail_reminderWealthRegitration(compCode)

    # Tax Consent reminding
    utils.reminderTaxConsent(compCode)

    # Suit dialy report
    utils.sendMail_SuitDialyReport(compCode)


    return msg

# Read more https://apscheduler.readthedocs.io/en/stable/modules/triggers/cron.html#module-apscheduler.triggers.cron
# https://apscheduler.readthedocs.io/en/3.x/userguide.html

def start():
    scheduler = BackgroundScheduler()

#     try:
#         scheduler.remove_job('job_sch_dialy')
#     except Exception as e:
#         print(' Was error >> %s' % type(e))

#     scheduler.add_job(job_function, "cron", day_of_week='mon-fri',
#                       hour=8, minute='0', id="job_sch_dialy", replace_existing=True)
#     # scheduler.add_job(job_function, "interval",minutes=1,id="job_sch_dialy",replace_existing=True)
    scheduler.start()
