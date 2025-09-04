from datetime import date

def qdate_to_iso(qdate):
    """QDate -> "YYYY-MM-DD" string"""
    return f"{qdate.year():04d}-{qdate.month():02d}-{qdate.day():02d}"

def today_iso():
    d = date.today()
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"