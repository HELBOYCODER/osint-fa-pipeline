import ephem
# usage: python moon.py <lat> <lon> <YYYY-MM-DD> <HH:MM local> <tz_offset_hours>
import sys
lat, lon = sys.argv[1], sys.argv[2]
y, mo, d = (int(v) for v in sys.argv[3].split('-'))
hh, mm = (int(v) for v in sys.argv[4].split(':'))
tz = float(sys.argv[5])
obs = ephem.Observer()
obs.lat, obs.lon = lat, lon
obs.date = ephem.date((y, mo, d, hh - tz, mm, 0))  # convert local → UTC
m = ephem.Moon()
m.compute(obs)
print('moon azimuth :', round(float(ephem.degrees(m.az)), 1), 'deg (N=0, E=90)')
print('moon altitude:', round(float(ephem.degrees(m.alt)), 1), 'deg')
print('phase        :', round(m.phase), '%')
