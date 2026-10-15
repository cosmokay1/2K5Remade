"""Cross-check guest float32/truncation across native and Python implementations."""
import json
from pathlib import Path
import subprocess
import sys

from franchise.guest_contracts import GuestContractTerms, GUEST_CONTRACT_FORMAT, SOFTDRINK_CONTRACT_FORMAT


def main():
    build=Path(sys.argv[1])
    executable=build/('Release/franchise_protocol_check.exe' if sys.platform=='win32' else 'franchise_protocol_check')
    if sys.platform=='win32' and not executable.is_file():
        executable=build/'franchise_protocol_check.exe'  # Ninja private Windows build.
    samples=[]
    for contract_format in (GUEST_CONTRACT_FORMAT,SOFTDRINK_CONTRACT_FORMAT):
        for amount in (1,10,500,600,829,65535):
            for years in range(1,16):
                for shape in range(8):
                    for bonus in (0,1,4,10):
                        flags=(shape<<29)|(years<<16)|bonus|0x0D000000
                        try:
                            offer=GuestContractTerms.from_context(amount,flags).to_offer('synthetic-guest',contract_format=contract_format).to_dict()
                        except ValueError:
                            offer=None
                        samples.append({'contract_format':contract_format,'raw':{'amount_word':amount,'flags_word':flags},'player_id':'synthetic-guest','offer':offer})
    for amount,flags in ((0,2<<16),(65536,2<<16),(True,2<<16),(1,-1),(1,2**32),(1,False)):
        samples.append({'raw':{'amount_word':amount,'flags_word':flags},'player_id':'synthetic-guest','offer':None})
    samples.append({'contract_format':'unknown','raw':{'amount_word':829,'flags_word':(2<<16)|4},
                    'player_id':'synthetic-guest','offer':None})
    completed=subprocess.run([str(executable),'--guest-terms'],input=''.join(json.dumps(s)+'\n' for s in samples),
                             text=True,capture_output=True,check=True,timeout=30,
                             creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=='win32' else 0)
    print(completed.stdout,end='')


if __name__=='__main__':
    main()
