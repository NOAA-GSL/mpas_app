import sys
from datetime import datetime


now = datetime.now()
now = now.time()

begin = sys.argv[1]
end = sys.argv[2]

begin = datetime.strptime(begin, "%H:%M:%S").time()
end = datetime.strptime(end, "%H:%M:%S").time()

if end < begin:
    if now > begin or now < end:
        sys.exit(0)

if now > begin and now < end:
    sys.exit(0)
sys.exit(1)

