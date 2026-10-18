import datetime
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('broadcast_networks', ROOT / 'tools/presentation-studio/networks.py')
networks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(networks)


def record(date='2026-09-13', hour=1, home=15, away=11, minute=0):
    day = datetime.date.fromisoformat(date)
    return bytes((0, home, away, day.month, day.day, day.year-2000, hour, minute))


def fixture():
    from tests.test_inspect_franchise_calendar import CalendarTests
    data = CalendarTests().fixture()
    struct.pack_into('<I', data, 0x348, 272)
    data[0x91321] = 8
    grid = 0x91320+0x4CA
    data[grid:grid+8] = record()
    return data


class NetworkPolicyTests(unittest.TestCase):
    def test_windows_conferences_and_holidays(self):
        cases = [('2026-09-13',1,15,11,0,'FOX'), ('2026-09-13',4,15,3,25,'CBS'),
                 ('2026-09-13',8,15,11,20,'NBC'), ('2026-09-14',8,15,11,15,'ESPN'),
                 ('2026-10-15',8,15,11,15,'Prime'), ('2026-09-10',8,15,11,20,'NBC'),
                 ('2026-11-26',0,18,11,30,'CBS'), ('2026-11-26',4,11,15,30,'FOX'),
                 ('2026-11-26',8,15,11,20,'NBC'), ('2026-12-19',4,15,11,30,'NFL Network'),
                 ('2026-10-18',9,15,11,30,'NFL Network')]
        for date,hour,home,away,minute,want in cases:
            with self.subTest(date=date,hour=hour):
                self.assertEqual(networks.assignment(record(date,hour,home,away,minute))[0],want)

    def test_preseason_is_regional_not_prime(self):
        raw = record('2026-08-06',8,home=15,away=3)
        self.assertEqual(networks.assignment(raw,preseason=True)[0], 'FOX')
        self.assertEqual(networks.assignment(raw)[0], 'Prime')

    def test_played_status_does_not_change_identity(self):
        before=fixture();after=bytearray(before);after[0x91320+0x4CA]=3
        a=networks.read_schedule(bytes(before));b=networks.read_schedule(bytes(after))
        self.assertEqual(a['games'][0]['key'], b['games'][0]['key'])
        after[0x91320+6]+=1
        self.assertNotEqual(a['token'],networks.read_schedule(bytes(after))['token'])

    def test_schedule_change_is_a_new_identity(self):
        before=fixture();after=bytearray(before);after[0x91320+0x4CA+2]=3
        self.assertNotEqual(networks.read_schedule(bytes(before))['token'],networks.read_schedule(bytes(after))['token'])

    def test_bad_saves_and_future_playoff_placeholders(self):
        with self.assertRaises(ValueError):networks.read_schedule(b'bad')
        data=fixture();grid=0x91320+0x4CA
        data[grid+18*17*8:grid+18*17*8+8]=bytes((0,0,0,1,1,27,8,0))
        self.assertEqual(len(networks.read_schedule(bytes(data))['games']),1)

    def test_override_roundtrip_keeps_previous_season(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'networks.json'
            settings=networks.load_settings(path)
            settings['overrides']={'old-season-game':'FOX','new-season-game':'CBS'}
            networks.save_settings(path,settings)
            self.assertEqual(networks.load_settings(path),settings)
            self.assertFalse(path.with_suffix('.tmp').exists())


class NativeParityTests(unittest.TestCase):
    def test_cpp_policy_and_identity_match_python_for_whole_calendar(self):
        compiler=shutil.which('c++') or shutil.which('clang++')
        if not compiler:self.skipTest('C++ compiler unavailable')
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'check.cpp';binary=Path(temp)/'check'
            source.write_text('''#include "broadcast_schedule.h"
#include <iostream>
int main(){int y,m,d,h,minute,home,away,phase;
while(std::cin>>y>>m>>d>>h>>minute>>home>>away>>phase){unsigned char g[]={0,(unsigned char)home,(unsigned char)away,(unsigned char)m,(unsigned char)d,(unsigned char)(y-2000),(unsigned char)h,(unsigned char)minute};
std::cout<<broadcast_schedule::network(g,phase==9,phase==7)<<"\\n";}
unsigned char grid[22*17*8]={};unsigned char g[]={0,15,11,9,13,26,1,0};for(int i=0;i<8;++i)grid[i]=g[i];
std::cout<<broadcast_schedule::token(grid,0,18)<<"\\n";
}''')
            subprocess.run([compiler,'-std=c++17','-I',str(ROOT/'src'),str(source),'-o',str(binary)],check=True,capture_output=True)
            cases=[];expected=[]
            for offset in range(366):
                day=datetime.date(2026,1,1)+datetime.timedelta(days=offset)
                for hour,minute in ((0,0),(1,0),(4,25),(8,20),(9,30)):
                    for phase in (7,8,9):
                        raw=record(day.isoformat(),hour,15,3,minute)
                        cases.append(f'{day.year} {day.month} {day.day} {hour} {minute} 15 3 {phase}')
                        expected.append(networks.assignment(raw,phase==9,phase==7)[0])
            result=subprocess.run([str(binary)],input='\n'.join(cases)+'\n',text=True,capture_output=True,check=True).stdout.splitlines()
            self.assertEqual(result[:-1],expected)
            grid=record()+bytes(22*17*8-8)
            self.assertEqual(result[-1],networks.schedule_token(grid,0,18))


if __name__=='__main__':unittest.main()
