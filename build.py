#!/usr/bin/env python3
"""
appbuilder_build.py — baut die "App Builder"-App selbst als Android-APK.

Eigenstaendig: die Builder-Oberflaeche (HTML) ist eingebettet. Als native App
kann der Builder nativen HTTP (kein CORS) nutzen und APKs in einen lokalen
Ordner speichern (ein Ordner pro App, alle Versionen darin).

  python appbuilder_build.py            # Projekt bauen + synchronisieren
  python appbuilder_build.py --apk      # zusaetzlich Debug-APK bauen

Voraussetzungen: Node.js 22+, Android Studio (Android SDK + JDK).
"""
import argparse
import base64
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"


def log(m): print(f"\033[36m> {m}\033[0m")
def ok(m): print(f"\033[32m\u2713 {m}\033[0m")
def warn(m): print(f"\033[33m! {m}\033[0m")
def fail(m): print(f"\033[31m\u2717 {m}\033[0m"); sys.exit(1)


def tool(n):
    return shutil.which(n) or (shutil.which(n + ".cmd") if IS_WINDOWS else None)


def run(cmd, cwd=None):
    log(" ".join(str(c) for c in cmd) + (f"   ({cwd})" if cwd else ""))
    if subprocess.run(cmd, cwd=cwd).returncode != 0:
        fail("Kommando fehlgeschlagen: " + " ".join(str(c) for c in cmd))


# Eingebettete Builder-Oberflaeche (base64).
INDEX_HTML_B64 = "PCFET0NUWVBFIGh0bWw+CjxodG1sIGxhbmc9ImRlIj4KPGhlYWQ+CjxtZXRhIGNoYXJzZXQ9IlVURi04IiAvPgo8bWV0YSBuYW1lPSJ2aWV3cG9ydCIgY29udGVudD0id2lkdGg9ZGV2aWNlLXdpZHRoLCBpbml0aWFsLXNjYWxlPTEsIHZpZXdwb3J0LWZpdD1jb3ZlciIgLz4KPHRpdGxlPkFwcCBCdWlsZGVyPC90aXRsZT4KPHN0eWxlPgogIDpyb290ey0tYmc6I0VERjBGNTstLXBhbmVsOiNmZmY7LS1wYW5lbDI6I0YyRjVGOTstLWxpbmU6I0Q2RERFODstLXRleHQ6IzE4MjEyRTstLW11dGVkOiM1QTY2NzY7LS1hY2NlbnQ6IzFFOUU3QzstLWVycjojQ0UzQTJBfQogICp7Ym94LXNpemluZzpib3JkZXItYm94O21hcmdpbjowO3BhZGRpbmc6MH0KICBib2R5e2JhY2tncm91bmQ6dmFyKC0tYmcpO2NvbG9yOnZhcigtLXRleHQpO2ZvbnQtZmFtaWx5OnN5c3RlbS11aSwtYXBwbGUtc3lzdGVtLCJTZWdvZSBVSSIsUm9ib3RvLHNhbnMtc2VyaWY7cGFkZGluZzoxNnB4IDE2cHggY2FsYyhlbnYoc2FmZS1hcmVhLWluc2V0LWJvdHRvbSkgKyAyNHB4KTttYXgtd2lkdGg6NTIwcHg7bWFyZ2luOjAgYXV0b30KICBoMXtmb250LXNpemU6MjJweDttYXJnaW4tYm90dG9tOjRweH0KICAuc3Vie2NvbG9yOnZhcigtLW11dGVkKTtmb250LXNpemU6MTNweDttYXJnaW4tYm90dG9tOjE0cHh9CiAgLnN0YXR1c3tmb250LXNpemU6MTJweDtwYWRkaW5nOjVweCAxMHB4O2JvcmRlci1yYWRpdXM6OTk5cHg7ZGlzcGxheTppbmxpbmUtYmxvY2s7bWFyZ2luLWJvdHRvbToxNHB4O2JhY2tncm91bmQ6dmFyKC0tcGFuZWwpO2JvcmRlcjoxcHggc29saWQgdmFyKC0tbGluZSl9CiAgLnN0YXR1c1tkYXRhLW9rPSJ0cnVlIl17YmFja2dyb3VuZDpjb2xvci1taXgoaW4gc3JnYix2YXIoLS1hY2NlbnQpIDE0JSx2YXIoLS1wYW5lbCkpO2JvcmRlci1jb2xvcjp2YXIoLS1hY2NlbnQpO2NvbG9yOiMwYjdhNWN9CiAgLmNhcmR7YmFja2dyb3VuZDp2YXIoLS1wYW5lbCk7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtib3JkZXItcmFkaXVzOjE0cHg7cGFkZGluZzoxNnB4O21hcmdpbi1ib3R0b206MTRweH0KICAuY2FyZCBoMntmb250LXNpemU6MTVweDttYXJnaW4tYm90dG9tOjEwcHg7ZGlzcGxheTpmbGV4O2p1c3RpZnktY29udGVudDpzcGFjZS1iZXR3ZWVuO2FsaWduLWl0ZW1zOmNlbnRlcn0KICBsYWJlbHtkaXNwbGF5OmJsb2NrO2ZvbnQtc2l6ZToxMnB4O2NvbG9yOnZhcigtLW11dGVkKTttYXJnaW46MTBweCAwIDRweH0KICBpbnB1dFt0eXBlPXRleHRdLGlucHV0W3R5cGU9cGFzc3dvcmRde3dpZHRoOjEwMCU7YmFja2dyb3VuZDp2YXIoLS1wYW5lbDIpO2JvcmRlcjoxcHggc29saWQgdmFyKC0tbGluZSk7Y29sb3I6dmFyKC0tdGV4dCk7Ym9yZGVyLXJhZGl1czo5cHg7cGFkZGluZzoxMXB4IDEycHg7Zm9udC1zaXplOjE1cHh9CiAgaW5wdXQ6Zm9jdXN7b3V0bGluZTpub25lO2JvcmRlci1jb2xvcjp2YXIoLS1hY2NlbnQpfQogIC5maWxle2Rpc3BsYXk6YmxvY2s7d2lkdGg6MTAwJTtiYWNrZ3JvdW5kOnZhcigtLXBhbmVsMik7Ym9yZGVyOjFweCBkYXNoZWQgdmFyKC0tbGluZSk7Ym9yZGVyLXJhZGl1czo5cHg7cGFkZGluZzoxNHB4O3RleHQtYWxpZ246Y2VudGVyO2ZvbnQtc2l6ZToxNHB4O2NvbG9yOnZhcigtLW11dGVkKTtjdXJzb3I6cG9pbnRlcn0KICAuYnRue3dpZHRoOjEwMCU7YmFja2dyb3VuZDp2YXIoLS1hY2NlbnQpO2NvbG9yOiNmZmY7Ym9yZGVyOm5vbmU7Ym9yZGVyLXJhZGl1czoxMXB4O3BhZGRpbmc6MTRweDtmb250LXNpemU6MTZweDtmb250LXdlaWdodDo2MDA7Y3Vyc29yOnBvaW50ZXI7bWFyZ2luLXRvcDoxMnB4fQogIC5idG46ZGlzYWJsZWR7YmFja2dyb3VuZDojQjdDMkQwO2N1cnNvcjpub3QtYWxsb3dlZH0KICAuYnRuLnNlY3tiYWNrZ3JvdW5kOnZhcigtLXBhbmVsMik7Y29sb3I6dmFyKC0tdGV4dCk7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKX0KICAuYnRuLmRhbmdlcntiYWNrZ3JvdW5kOnRyYW5zcGFyZW50O2NvbG9yOnZhcigtLWVycik7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1lcnIpfQogIC5yb3d7ZGlzcGxheTpmbGV4O2dhcDo4cHh9LnJvdz4qe2ZsZXg6MX0KICAubGlua3tjb2xvcjp2YXIoLS1hY2NlbnQpO2ZvbnQtc2l6ZToxM3B4O3RleHQtZGVjb3JhdGlvbjpub25lfQogIC5ub3Rle2ZvbnQtc2l6ZToxMXB4O2NvbG9yOnZhcigtLW11dGVkKTttYXJnaW4tdG9wOjEwcHg7bGluZS1oZWlnaHQ6MS41fQogIC5sb2d7YmFja2dyb3VuZDojMEUxMzFDO2NvbG9yOiNDQkQ1RTE7Ym9yZGVyLXJhZGl1czoxMHB4O3BhZGRpbmc6MTJweDtmb250LWZhbWlseTp1aS1tb25vc3BhY2UsbW9ub3NwYWNlO2ZvbnQtc2l6ZToxMnB4O2xpbmUtaGVpZ2h0OjEuNjt3aGl0ZS1zcGFjZTpwcmUtd3JhcDt3b3JkLWJyZWFrOmJyZWFrLXdvcmQ7bWF4LWhlaWdodDoyNDBweDtvdmVyZmxvdzphdXRvO21hcmdpbi10b3A6MTJweH0KICAubG9nIC5va3tjb2xvcjojNEFERTlBfS5sb2cgLmVycntjb2xvcjojRjg3MTcxfQogIC5kbHtkaXNwbGF5Om5vbmU7bWFyZ2luLXRvcDoxMnB4fQogIC5oaW50e2ZvbnQtc2l6ZToxMnB4O2NvbG9yOnZhcigtLW11dGVkKTttYXJnaW4tdG9wOjhweH0KICAuYXBwLWl0ZW17ZGlzcGxheTpmbGV4O2FsaWduLWl0ZW1zOmNlbnRlcjtnYXA6MTBweDtwYWRkaW5nOjExcHggMTJweDtib3JkZXI6MXB4IHNvbGlkIHZhcigtLWxpbmUpO2JvcmRlci1yYWRpdXM6MTFweDttYXJnaW4tYm90dG9tOjhweDtiYWNrZ3JvdW5kOnZhcigtLXBhbmVsMil9CiAgLmFpLW1haW57ZmxleDoxO21pbi13aWR0aDowfQogIC5haS1uYW1le2ZvbnQtd2VpZ2h0OjYwMDtmb250LXNpemU6MTVweH0KICAuYWktc3Vie2ZvbnQtc2l6ZToxMXB4O2NvbG9yOnZhcigtLW11dGVkKTt3aGl0ZS1zcGFjZTpub3dyYXA7b3ZlcmZsb3c6aGlkZGVuO3RleHQtb3ZlcmZsb3c6ZWxsaXBzaXN9CiAgLmFpLWFjdHtkaXNwbGF5OmZsZXg7Z2FwOjZweDtmbGV4LXNocmluazowfQogIC5jaGlwe2ZvbnQtc2l6ZToxMnB4O3BhZGRpbmc6N3B4IDEwcHg7Ym9yZGVyLXJhZGl1czo4cHg7Ym9yZGVyOjFweCBzb2xpZCB2YXIoLS1saW5lKTtiYWNrZ3JvdW5kOnZhcigtLXBhbmVsKTtjb2xvcjp2YXIoLS10ZXh0KTtjdXJzb3I6cG9pbnRlcjt0ZXh0LWRlY29yYXRpb246bm9uZTt3aGl0ZS1zcGFjZTpub3dyYXB9CiAgLmNoaXAuZGx7Ym9yZGVyLWNvbG9yOnZhcigtLWFjY2VudCk7Y29sb3I6IzBiN2E1Y30KICAuZW1wdHl7Y29sb3I6dmFyKC0tbXV0ZWQpO2ZvbnQtc2l6ZToxM3B4O3RleHQtYWxpZ246Y2VudGVyO3BhZGRpbmc6MTRweH0KICAuYWRkYnRue3dpZHRoOjEwMCU7Ym9yZGVyOjFweCBkYXNoZWQgdmFyKC0tbGluZSk7YmFja2dyb3VuZDp2YXIoLS1wYW5lbDIpO2NvbG9yOnZhcigtLXRleHQpO2JvcmRlci1yYWRpdXM6MTFweDtwYWRkaW5nOjEycHg7Zm9udC1zaXplOjE0cHg7Y3Vyc29yOnBvaW50ZXJ9CiAgI2VkaXRvcltoaWRkZW5de2Rpc3BsYXk6bm9uZX0KPC9zdHlsZT4KPC9oZWFkPgo8Ym9keT4KICA8aDE+8J+UpyBBcHAgQnVpbGRlcjwvaDE+CiAgPGRpdiBjbGFzcz0ic3ViIj5BcHBzIHZlcndhbHRlbiwgYmF1ZW4gdW5kIGFscyBBUEsgaGVydW50ZXJsYWRlbi48L2Rpdj4KICA8c3BhbiBjbGFzcz0ic3RhdHVzIiBpZD0ic3RhdHVzIiBkYXRhLW9rPSJmYWxzZSI+bmljaHQgdmVyYnVuZGVuPC9zcGFuPgoKICA8ZGl2IGNsYXNzPSJjYXJkIj4KICAgIDxoMj5HaXRIdWI8L2gyPgogICAgPGxhYmVsPlBlcnNvbmFsIEFjY2VzcyBUb2tlbjwvbGFiZWw+CiAgICA8aW5wdXQgdHlwZT0icGFzc3dvcmQiIGlkPSJwYXQiIHBsYWNlaG9sZGVyPSJnaHBf4oCmIC8gZ2l0aHViX3BhdF/igKYiIGF1dG9jb21wbGV0ZT0ib2ZmIiAvPgogICAgPGRpdiBjbGFzcz0iaGludCI+PGEgY2xhc3M9ImxpbmsiIGlkPSJ0b2tlbkxpbmsiIHRhcmdldD0iX2JsYW5rIiByZWw9Im5vb3BlbmVyIj5Ub2tlbiBlcnN0ZWxsZW4gKFNjb3BlczogcmVwbyArIHdvcmtmbG93KTwvYT48L2Rpdj4KICAgIDxidXR0b24gY2xhc3M9ImJ0biIgaWQ9ImNvbm5lY3QiPlZlcmJpbmRlbiAmYW1wOyBzcGVpY2hlcm48L2J1dHRvbj4KICAgIDxkaXYgY2xhc3M9Im5vdGUiPkRlciBUb2tlbiB3aXJkIG51ciBsb2thbCBhdWYgZGllc2VtIEdlcsOkdCBnZXNwZWljaGVydC4gTWluaW1hbGUgUmVjaHRlIChyZXBvICsgd29ya2Zsb3cpIGdlbsO8Z2VuOyBqZWRlcnplaXQgYXVmIEdpdEh1YiB3aWRlcnJ1ZmJhci48L2Rpdj4KICA8L2Rpdj4KCiAgPGRpdiBjbGFzcz0iY2FyZCI+CiAgICA8aDI+U3BlaWNoZXJvcmRuZXI8L2gyPgogICAgPGRpdiBjbGFzcz0iaGludCIgaWQ9ImZvbGRlck5hbWUiPlN0YW5kYXJkIChhcHAtZWlnZW5lciBPcmRuZXIpPC9kaXY+CiAgICA8ZGl2IGNsYXNzPSJyb3ciPgogICAgICA8YnV0dG9uIGNsYXNzPSJidG4gc2VjIiBpZD0icGlja0ZvbGRlciIgc3R5bGU9Im1hcmdpbi10b3A6MTBweCI+T3JkbmVyIHZlcmJpbmRlbjwvYnV0dG9uPgogICAgICA8YnV0dG9uIGNsYXNzPSJidG4gc2VjIiBpZD0icmVzZXRGb2xkZXIiIHN0eWxlPSJtYXJnaW4tdG9wOjEwcHgiPlN0YW5kYXJkPC9idXR0b24+CiAgICA8L2Rpdj4KICAgIDxkaXYgY2xhc3M9Im5vdGUiPlZlcmJpbmRlIGVpbmVuIGJlbGllYmlnZW4gT3JkbmVyICh6LkIuIGluIOKAnkRhdGVpZW4iIG9kZXIgZWluZW0gQ2xvdWQtT3JkbmVyKS4gSmVkZSBnZWJhdXRlIEFQSyBsYW5kZXQgZG9ydCB1bnRlciBhcHBzLyZsdDtBcHAmZ3Q7Ly4gTnVyIGluIGRlciBpbnN0YWxsaWVydGVuIEFwcC1CdWlsZGVyLUFwcC48L2Rpdj4KICA8L2Rpdj4KCiAgPGRpdiBjbGFzcz0iY2FyZCI+CiAgICA8aDI+TWVpbmUgQXBwczwvaDI+CiAgICA8ZGl2IGlkPSJhcHBMaXN0Ij48L2Rpdj4KICAgIDxidXR0b24gY2xhc3M9ImFkZGJ0biIgaWQ9Im5ld0FwcCI+KyBOZXVlIEFwcDwvYnV0dG9uPgogIDwvZGl2PgoKICA8ZGl2IGNsYXNzPSJjYXJkIiBpZD0iZWRpdG9yIiBoaWRkZW4+CiAgICA8aDI+PHNwYW4gaWQ9ImVkaXRvclRpdGxlIj5BcHA8L3NwYW4+PC9oMj4KICAgIDxsYWJlbD5BcHAtTmFtZTwvbGFiZWw+CiAgICA8aW5wdXQgdHlwZT0idGV4dCIgaWQ9ImFwcE5hbWUiIHBsYWNlaG9sZGVyPSJUcmFpbmVyIiAvPgogICAgPGRpdiBjbGFzcz0icm93Ij4KICAgICAgPGRpdj48bGFiZWw+QXBwLUlEIChQYWNrYWdlKTwvbGFiZWw+PGlucHV0IHR5cGU9InRleHQiIGlkPSJhcHBJZCIgcGxhY2Vob2xkZXI9ImNvbS5kZWlubmFtZS50cmFpbmVyIiAvPjwvZGl2PgogICAgICA8ZGl2PjxsYWJlbD5SZXBvLU5hbWU8L2xhYmVsPjxpbnB1dCB0eXBlPSJ0ZXh0IiBpZD0iYXBwUmVwbyIgcGxhY2Vob2xkZXI9InRyYWluZXItYXBwIiAvPjwvZGl2PgogICAgPC9kaXY+CiAgICA8bGFiZWw+QnVpbGQtU2tyaXB0ICgucHkgdm9uIENsYXVkZSk8L2xhYmVsPgogICAgPGxhYmVsIGNsYXNzPSJmaWxlIiBmb3I9ImZpbGUiIGlkPSJmaWxlTGFiZWwiPvCfk4QgU2tyaXB0IGxhZGVu4oCmPC9sYWJlbD4KICAgIDxpbnB1dCB0eXBlPSJmaWxlIiBpZD0iZmlsZSIgYWNjZXB0PSIucHkiIGhpZGRlbiAvPgogICAgPGJ1dHRvbiBjbGFzcz0iYnRuIiBpZD0iYnVpbGQiPkFQSyBiYXVlbjwvYnV0dG9uPgogICAgPGJ1dHRvbiBjbGFzcz0iYnRuIHNlYyIgaWQ9InNhdmUiPk51ciBzcGVpY2hlcm48L2J1dHRvbj4KICAgIDxidXR0b24gY2xhc3M9ImJ0biBkYW5nZXIiIGlkPSJkZWwiIHN0eWxlPSJkaXNwbGF5Om5vbmUiPkFwcCBsw7ZzY2hlbjwvYnV0dG9uPgogICAgPGRpdiBjbGFzcz0ibG9nIiBpZD0ibG9nIiBzdHlsZT0iZGlzcGxheTpub25lIj48L2Rpdj4KICAgIDxhIGNsYXNzPSJidG4gZGwiIGlkPSJkbCIgZG93bmxvYWQ+4qyHIEFQSyBoZXJ1bnRlcmxhZGVuPC9hPgogICAgPGEgY2xhc3M9ImxpbmsgZGwiIGlkPSJydW5MaW5rIiB0YXJnZXQ9Il9ibGFuayIgcmVsPSJub29wZW5lciIgc3R5bGU9InRleHQtYWxpZ246Y2VudGVyO21hcmdpbi10b3A6OHB4Ij5CdWlsZC1Mb2cgYXVmIEdpdEh1YiBhbnNlaGVuPC9hPgogICAgPGRpdiBpZD0idmVyc2lvbnNCb3giIHN0eWxlPSJtYXJnaW4tdG9wOjEycHgiPjwvZGl2PgogIDwvZGl2PgoKPHNjcmlwdCB0eXBlPSJ0ZXh0L3BsYWluIiBpZD0id2ZZYW1sIj4KbmFtZTogQnVpbGQgQVBLCm9uOgogIHdvcmtmbG93X2Rpc3BhdGNoOgogICAgaW5wdXRzOgogICAgICBhcHBfaWQ6CiAgICAgICAgZGVzY3JpcHRpb246ICJBcHAtSUQiCiAgICAgICAgZGVmYXVsdDogImNvbS5kZWlubmFtZS50cmFpbmVyIgogICAgICBhcHBfbmFtZToKICAgICAgICBkZXNjcmlwdGlvbjogIkFwcC1OYW1lIgogICAgICAgIGRlZmF1bHQ6ICJUcmFpbmVyIgpwZXJtaXNzaW9uczoKICBjb250ZW50czogd3JpdGUKam9iczoKICBidWlsZDoKICAgIHJ1bnMtb246IHVidW50dS1sYXRlc3QKICAgIHN0ZXBzOgogICAgICAtIHVzZXM6IGFjdGlvbnMvY2hlY2tvdXRAdjQKICAgICAgLSB1c2VzOiBhY3Rpb25zL3NldHVwLW5vZGVAdjQKICAgICAgICB3aXRoOgogICAgICAgICAgbm9kZS12ZXJzaW9uOiAiMjIiCiAgICAgIC0gdXNlczogYWN0aW9ucy9zZXR1cC1qYXZhQHY0CiAgICAgICAgd2l0aDoKICAgICAgICAgIGRpc3RyaWJ1dGlvbjogdGVtdXJpbgogICAgICAgICAgamF2YS12ZXJzaW9uOiAiMjEiCiAgICAgIC0gcnVuOiB5ZXMgfCAiJEFORFJPSURfSE9NRS9jbWRsaW5lLXRvb2xzL2xhdGVzdC9iaW4vc2RrbWFuYWdlciIgLS1saWNlbnNlcyB8fCB0cnVlCiAgICAgIC0gcnVuOiBweXRob24zIGJ1aWxkLnB5IC0tYXBrIC0tYXBwLWlkICIke3sgZ2l0aHViLmV2ZW50LmlucHV0cy5hcHBfaWQgfX0iIC0tYXBwLW5hbWUgIiR7eyBnaXRodWIuZXZlbnQuaW5wdXRzLmFwcF9uYW1lIH19IgogICAgICAtIG5hbWU6IFJlbGVhc2UgbWl0IEFQSwogICAgICAgIGVudjoKICAgICAgICAgIEdIX1RPS0VOOiAiJHt7IGdpdGh1Yi50b2tlbiB9fSIKICAgICAgICBydW46IHwKICAgICAgICAgIEFQSz0iJChmaW5kIC4gLXBhdGggJyovYXBrL2RlYnVnL2FwcC1kZWJ1Zy5hcGsnIHwgaGVhZCAtMSkiCiAgICAgICAgICBpZiBbIC16ICIkQVBLIiBdOyB0aGVuIGVjaG8gIktlaW5lIEFQSyBnZWZ1bmRlbiI7IGV4aXQgMTsgZmkKICAgICAgICAgIE5BTUU9IiR7eyBnaXRodWIuZXZlbnQuaW5wdXRzLmFwcF9uYW1lIH19IgogICAgICAgICAgY3AgIiRBUEsiICIkTkFNRS5hcGsiIHx8IGNwICIkQVBLIiBhcHAuYXBrCiAgICAgICAgICBGSUxFPSIkKGxzICouYXBrIHwgaGVhZCAtMSkiCiAgICAgICAgICBUQUc9ImJ1aWxkLSQoZGF0ZSArJVklbSVkLSVIJU0lUykiCiAgICAgICAgICBnaCByZWxlYXNlIGNyZWF0ZSAiJFRBRyIgIiRGSUxFIiAtLXRpdGxlICIkTkFNRSAkVEFHIiAtLW5vdGVzICJBdXRvbWF0aXNjaGVyIEJ1aWxkIiAtLWxhdGVzdAo8L3NjcmlwdD4KCjxzY3JpcHQ+CmNvbnN0IEFQST0iaHR0cHM6Ly9hcGkuZ2l0aHViLmNvbSI7CmNvbnN0ICQ9aWQ9PmRvY3VtZW50LmdldEVsZW1lbnRCeUlkKGlkKTsKY29uc3QgZXNjPXM9PlN0cmluZyhzPT1udWxsPyIiOnMpLnJlcGxhY2UoL1smPD4iXS9nLGM9Pih7IiYiOiImYW1wOyIsIjwiOiImbHQ7IiwiPiI6IiZndDsiLCJcIiI6IiZxdW90OyJ9W2NdKSk7CmNvbnN0IHNsdWc9cz0+KFN0cmluZyhzfHwiIikudG9Mb3dlckNhc2UoKS5yZXBsYWNlKC9bXlx3XSsvZywiLSIpLnJlcGxhY2UoL14tK3wtKyQvZywiIil8fCJhcHAiKTsKY29uc3Qgc2xlZXA9bXM9Pm5ldyBQcm9taXNlKHI9PnNldFRpbWVvdXQocixtcykpOwpjb25zdCBiNjQ9cz0+YnRvYSh1bmVzY2FwZShlbmNvZGVVUklDb21wb25lbnQocykpKTsKCmxldCBjZmc9e3BhdDoiIixvd25lcjoiIn07CmxldCBhcHBzPVtdOyAgICAgIC8vIHt1aWQsbmFtZSxwa2cscmVwbyxzY3JpcHROYW1lLHNjcmlwdCxhcGtVcmwsdmVyc2lvbnN9CmxldCBjdXI9bnVsbDsgICAgIC8vIGFrdHVlbGwgYmVhcmJlaXRldGUgQXBwCgovLyBMw6R1ZnQgZGllIE9iZXJmbMOkY2hlIGFscyBpbnN0YWxsaWVydGUgQXBwIChDYXBhY2l0b3IpPyBEYW5uIGxva2FsIHNwZWljaGVybiBtw7ZnbGljaC4KY29uc3QgTkFUSVZFPSEhKHdpbmRvdy5DYXBhY2l0b3IgJiYgd2luZG93LkNhcGFjaXRvci5pc05hdGl2ZVBsYXRmb3JtICYmIHdpbmRvdy5DYXBhY2l0b3IuaXNOYXRpdmVQbGF0Zm9ybSgpKTsKZnVuY3Rpb24gZnNQbHVnaW4oKXtyZXR1cm4gd2luZG93LkNhcGFjaXRvciYmd2luZG93LkNhcGFjaXRvci5QbHVnaW5zP3dpbmRvdy5DYXBhY2l0b3IuUGx1Z2lucy5GaWxlc3lzdGVtOm51bGw7fQoKbGV0IGZvbGRlcj1udWxsOyAgLy8gZ2V3w6RobHRlciBTQUYtT3JkbmVyIHt1cmksbmFtZX0gb2RlciBudWxsID0gU3RhbmRhcmQKZnVuY3Rpb24gc2FmUGx1Z2luKCl7cmV0dXJuIHdpbmRvdy5DYXBhY2l0b3ImJndpbmRvdy5DYXBhY2l0b3IuUGx1Z2lucz93aW5kb3cuQ2FwYWNpdG9yLlBsdWdpbnMuU2FmRm9sZGVyOm51bGw7fQpmdW5jdGlvbiB1cGRhdGVGb2xkZXJVSSgpe2NvbnN0IGVsPSQoImZvbGRlck5hbWUiKTtpZighZWwpcmV0dXJuO2VsLnRleHRDb250ZW50PWZvbGRlciYmZm9sZGVyLm5hbWU/KCJPcmRuZXI6ICIrZm9sZGVyLm5hbWUpOiJTdGFuZGFyZCAoYXBwLWVpZ2VuZXIgT3JkbmVyKSI7fQoKYXN5bmMgZnVuY3Rpb24gc2F2ZUFwa0xvY2FsbHkoYXBwLHVybCl7CiAgY29uc3QgRlM9ZnNQbHVnaW4oKTtpZighTkFUSVZFfHwhRlMpcmV0dXJuIG51bGw7CiAgY29uc3Qgc3RhbXA9bmV3IERhdGUoKS50b0lTT1N0cmluZygpLnJlcGxhY2UoL1s6VF0vZywiLSIpLnNsaWNlKDAsMTYpOwogIGNvbnN0IGZpbGU9c2x1ZyhhcHAubmFtZSkrIi0iK3N0YW1wKyIuYXBrIjsKICBjb25zdCBTQUY9c2FmUGx1Z2luKCk7CiAgaWYoZm9sZGVyJiZmb2xkZXIudXJpJiZTQUYpewogICAgLy8gSW4gZGVuIGdld8OkaGx0ZW4gT3JkbmVyIChTQUYpOiBlcnN0IGluIENhY2hlIGxhZGVuLCBkYW5uIGhpbmVpbmtvcGllcmVuCiAgICBjb25zdCB0bXA9InRtcC8iK2ZpbGU7CiAgICBhd2FpdCBGUy5kb3dubG9hZEZpbGUoe3VybCxwYXRoOnRtcCxkaXJlY3Rvcnk6IkNBQ0hFIixyZWN1cnNpdmU6dHJ1ZX0pOwogICAgY29uc3Qgc3JjPShhd2FpdCBGUy5nZXRVcmkoe2RpcmVjdG9yeToiQ0FDSEUiLHBhdGg6dG1wfSkpLnVyaTsKICAgIGNvbnN0IHI9YXdhaXQgU0FGLnNhdmVUb0ZvbGRlcih7dHJlZVVyaTpmb2xkZXIudXJpLHN1YkRpcjpzbHVnKGFwcC5uYW1lKSxmaWxlTmFtZTpmaWxlLHNyY1BhdGg6c3JjfSk7CiAgICB0cnl7YXdhaXQgRlMuZGVsZXRlRmlsZSh7ZGlyZWN0b3J5OiJDQUNIRSIscGF0aDp0bXB9KTt9Y2F0Y2goZSl7fQogICAgcmV0dXJuIHtmaWxlLHBhdGg6KGZvbGRlci5uYW1lfHwiT3JkbmVyIikrIi9hcHBzLyIrc2x1ZyhhcHAubmFtZSkrIi8iK2ZpbGUsdXJpOnIudXJpLGRhdGU6RGF0ZS5ub3coKX07CiAgfQogIC8vIFN0YW5kYXJkOiBhcHAtZWlnZW5lciBPcmRuZXIKICBjb25zdCBwYXRoPSJhcHBzLyIrc2x1ZyhhcHAubmFtZSkrIi8iK2ZpbGU7CiAgYXdhaXQgRlMuZG93bmxvYWRGaWxlKHt1cmwscGF0aCxkaXJlY3Rvcnk6IkVYVEVSTkFMIixyZWN1cnNpdmU6dHJ1ZX0pOwogIGNvbnN0IHVyaT0oYXdhaXQgRlMuZ2V0VXJpKHtkaXJlY3Rvcnk6IkVYVEVSTkFMIixwYXRofSkpLnVyaTsKICByZXR1cm4ge2ZpbGUscGF0aCx1cmksZGF0ZTpEYXRlLm5vdygpfTsKfQphc3luYyBmdW5jdGlvbiBzaGFyZUZpbGUodXJpKXsKICB0cnl7YXdhaXQgd2luZG93LkNhcGFjaXRvci5QbHVnaW5zLlNoYXJlLnNoYXJlKHt0aXRsZToiQVBLIix1cmw6dXJpfSk7fQogIGNhdGNoKGUpe2FsZXJ0KCLDlmZmbmVuL1RlaWxlbiBuaWNodCBtw7ZnbGljaDogIisoZS5tZXNzYWdlfHxlKSk7fQp9CmZ1bmN0aW9uIHJlbmRlclZlcnNpb25zKGFwcCl7CiAgY29uc3QgZWw9JCgidmVyc2lvbnNCb3giKTtpZighZWwpcmV0dXJuOwogIGlmKCFOQVRJVkUpe2VsLmlubmVySFRNTD0nPGRpdiBjbGFzcz0ibm90ZSI+TG9rYWxlcyBTcGVpY2hlcm4gZ2lidCBlcyBudXIgaW4gZGVyIGluc3RhbGxpZXJ0ZW4gQXBwLUJ1aWxkZXItQXBwIChuaWNodCBpbSBCcm93c2VyKS48L2Rpdj4nO3JldHVybjt9CiAgY29uc3QgdnM9KGFwcCYmYXBwLnZlcnNpb25zKXx8W107CiAgaWYoIXZzLmxlbmd0aCl7ZWwuaW5uZXJIVE1MPSc8ZGl2IGNsYXNzPSJub3RlIj5Ob2NoIGtlaW5lIGxva2FsIGdlc3BlaWNoZXJ0ZW4gVmVyc2lvbmVuLiBOYWNoIGRlbSBCYXVlbiBsYW5kZXQgamVkZSBWZXJzaW9uIGltIE9yZG5lciBhcHBzLycrc2x1ZygoYXBwJiZhcHAubmFtZSl8fCJhcHAiKSsnLy48L2Rpdj4nO3JldHVybjt9CiAgZWwuaW5uZXJIVE1MPSc8ZGl2IHN0eWxlPSJmb250LXNpemU6MTJweDtjb2xvcjp2YXIoLS1tdXRlZCk7bWFyZ2luLWJvdHRvbTo2cHgiPkdlc3BlaWNoZXJ0ZSBWZXJzaW9uZW4gKCcrdnMubGVuZ3RoKycpIMK3IGFwcHMvJytzbHVnKGFwcC5uYW1lKSsnLzwvZGl2PicrCiAgICB2cy5zbGljZSgpLnJldmVyc2UoKS5tYXAodj0+YDxkaXYgY2xhc3M9ImFwcC1pdGVtIj48ZGl2IGNsYXNzPSJhaS1tYWluIj48ZGl2IGNsYXNzPSJhaS1uYW1lIiBzdHlsZT0iZm9udC1zaXplOjEzcHgiPiR7ZXNjKG5ldyBEYXRlKHYuZGF0ZSkudG9Mb2NhbGVTdHJpbmcoKSl9PC9kaXY+PGRpdiBjbGFzcz0iYWktc3ViIj4ke2VzYyh2LmZpbGUpfTwvZGl2PjwvZGl2PjxkaXYgY2xhc3M9ImFpLWFjdCI+PGJ1dHRvbiBjbGFzcz0iY2hpcCIgZGF0YS1zaGFyZT0iJHtlc2Modi51cmkpfSI+w5ZmZm5lbjwvYnV0dG9uPjwvZGl2PjwvZGl2PmApLmpvaW4oIiIpOwogIGVsLnF1ZXJ5U2VsZWN0b3JBbGwoIltkYXRhLXNoYXJlXSIpLmZvckVhY2goYj0+Yi5vbmNsaWNrPSgpPT5zaGFyZUZpbGUoYi5kYXRhc2V0LnNoYXJlKSk7Cn0KCiQoInRva2VuTGluayIpLmhyZWY9Imh0dHBzOi8vZ2l0aHViLmNvbS9zZXR0aW5ncy90b2tlbnMvbmV3P3Njb3Blcz1yZXBvLHdvcmtmbG93JmRlc2NyaXB0aW9uPUFwcCtCdWlsZGVyIjsKCmZ1bmN0aW9uIGxvYWRBbGwoKXsKICB0cnl7T2JqZWN0LmFzc2lnbihjZmcsSlNPTi5wYXJzZShsb2NhbFN0b3JhZ2UuZ2V0SXRlbSgiYWJfY2ZnIil8fCJ7fSIpKTt9Y2F0Y2goZSl7fQogIHRyeXthcHBzPUpTT04ucGFyc2UobG9jYWxTdG9yYWdlLmdldEl0ZW0oImFiX2FwcHMiKXx8IltdIik7aWYoIUFycmF5LmlzQXJyYXkoYXBwcykpYXBwcz1bXTt9Y2F0Y2goZSl7YXBwcz1bXTt9CiAgdHJ5e2ZvbGRlcj1KU09OLnBhcnNlKGxvY2FsU3RvcmFnZS5nZXRJdGVtKCJhYl9mb2xkZXIiKXx8Im51bGwiKTt9Y2F0Y2goZSl7Zm9sZGVyPW51bGw7fQp9CmZ1bmN0aW9uIHNhdmVDZmcoKXt0cnl7bG9jYWxTdG9yYWdlLnNldEl0ZW0oImFiX2NmZyIsSlNPTi5zdHJpbmdpZnkoY2ZnKSk7fWNhdGNoKGUpe319CmZ1bmN0aW9uIHNhdmVBcHBzKCl7dHJ5e2xvY2FsU3RvcmFnZS5zZXRJdGVtKCJhYl9hcHBzIixKU09OLnN0cmluZ2lmeShhcHBzKSk7fWNhdGNoKGUpe2FsZXJ0KCJTcGVpY2hlciB2b2xsIOKAlCB6dSB2aWVsZS9ncm/Dn2UgU2tyaXB0ZS4iKTt9fQpmdW5jdGlvbiBzZXRDb25uKG9rKXskKCJzdGF0dXMiKS5kYXRhc2V0Lm9rPW9rPyJ0cnVlIjoiZmFsc2UiOyQoInN0YXR1cyIpLnRleHRDb250ZW50PW9rPygidmVyYnVuZGVuOiAiK2NmZy5vd25lcik6Im5pY2h0IHZlcmJ1bmRlbiI7fQoKZnVuY3Rpb24gbG9nKG1zZyxjbHMpe2NvbnN0IGw9JCgibG9nIik7bC5zdHlsZS5kaXNwbGF5PSJibG9jayI7Y29uc3QgZD1kb2N1bWVudC5jcmVhdGVFbGVtZW50KCJkaXYiKTtpZihjbHMpZC5jbGFzc05hbWU9Y2xzO2QudGV4dENvbnRlbnQ9bXNnO2wuYXBwZW5kQ2hpbGQoZCk7bC5zY3JvbGxUb3A9bC5zY3JvbGxIZWlnaHQ7fQpmdW5jdGlvbiBjbGVhckxvZygpeyQoImxvZyIpLmlubmVySFRNTD0iIjskKCJsb2ciKS5zdHlsZS5kaXNwbGF5PSJub25lIjt9Cgphc3luYyBmdW5jdGlvbiBnaChtZXRob2QscGF0aCxib2R5KXsKICBjb25zdCByZXM9YXdhaXQgZmV0Y2goQVBJK3BhdGgse21ldGhvZCxoZWFkZXJzOnsKICAgICJBdXRob3JpemF0aW9uIjoiQmVhcmVyICIrY2ZnLnBhdCwiQWNjZXB0IjoiYXBwbGljYXRpb24vdm5kLmdpdGh1Yitqc29uIiwiWC1HaXRIdWItQXBpLVZlcnNpb24iOiIyMDIyLTExLTI4IiwKICAgIC4uLihib2R5P3siQ29udGVudC1UeXBlIjoiYXBwbGljYXRpb24vanNvbiJ9Ont9KX0sYm9keTpib2R5P0pTT04uc3RyaW5naWZ5KGJvZHkpOnVuZGVmaW5lZH0pOwogIGxldCBkYXRhPW51bGw7dHJ5e2RhdGE9YXdhaXQgcmVzLmpzb24oKTt9Y2F0Y2goZSl7fQogIHJldHVybiB7b2s6cmVzLm9rLHN0YXR1czpyZXMuc3RhdHVzLGRhdGF9Owp9CgovLyAtLS0tIEdpdEh1Yi1WZXJiaW5kZW4gLS0tLQokKCJjb25uZWN0Iikub25jbGljaz1hc3luYygpPT57CiAgY2ZnLnBhdD0kKCJwYXQiKS52YWx1ZS50cmltKCk7CiAgaWYoIWNmZy5wYXQpe2FsZXJ0KCJCaXR0ZSBUb2tlbiBlaW5nZWJlbi4iKTtyZXR1cm47fQogIHRyeXsKICAgIGNvbnN0IHU9YXdhaXQgZ2goIkdFVCIsIi91c2VyIik7CiAgICBpZih1LnN0YXR1cyE9PTIwMCl7c2V0Q29ubihmYWxzZSk7YWxlcnQoIlRva2VuIHVuZ8O8bHRpZyAoIit1LnN0YXR1cysiKS4iKTtyZXR1cm47fQogICAgY2ZnLm93bmVyPXUuZGF0YS5sb2dpbjtzYXZlQ2ZnKCk7c2V0Q29ubih0cnVlKTsKICB9Y2F0Y2goZSl7YWxlcnQoIk5ldHp3ZXJrLS9DT1JTLUZlaGxlcjogIisoZS5tZXNzYWdlfHxlKSsiXG5GYWxscyBkZXIgQnJvd3NlciBHaXRIdWIgYmxvY2t0LCBEYXRlaSBob3N0ZW4gKHNpZWhlIEFubGVpdHVuZykuIik7fQp9OwoKLy8gLS0tLSBTcGVpY2hlcm9yZG5lciAoU0FGKSAtLS0tCiQoInBpY2tGb2xkZXIiKS5vbmNsaWNrPWFzeW5jKCk9PnsKICBjb25zdCBTQUY9c2FmUGx1Z2luKCk7CiAgaWYoIU5BVElWRXx8IVNBRil7YWxlcnQoIk51ciBpbiBkZXIgaW5zdGFsbGllcnRlbiBBcHAtQnVpbGRlci1BcHAgdmVyZsO8Z2Jhci4iKTtyZXR1cm47fQogIHRyeXtjb25zdCByPWF3YWl0IFNBRi5waWNrRm9sZGVyKCk7Zm9sZGVyPXt1cmk6ci51cmksbmFtZTpyLm5hbWV9O2xvY2FsU3RvcmFnZS5zZXRJdGVtKCJhYl9mb2xkZXIiLEpTT04uc3RyaW5naWZ5KGZvbGRlcikpO3VwZGF0ZUZvbGRlclVJKCk7fQogIGNhdGNoKGUpey8qIGFiZ2Vicm9jaGVuICovfQp9OwokKCJyZXNldEZvbGRlciIpLm9uY2xpY2s9KCk9Pntmb2xkZXI9bnVsbDtsb2NhbFN0b3JhZ2UucmVtb3ZlSXRlbSgiYWJfZm9sZGVyIik7dXBkYXRlRm9sZGVyVUkoKTt9OwoKLy8gLS0tLSBMaXN0ZSAtLS0tCmZ1bmN0aW9uIHJlbmRlckFwcHMoKXsKICBjb25zdCBlbD0kKCJhcHBMaXN0Iik7CiAgaWYoIWFwcHMubGVuZ3RoKXtlbC5pbm5lckhUTUw9JzxkaXYgY2xhc3M9ImVtcHR5Ij5Ob2NoIGtlaW5lIEFwcHMuIFRpcHBlIOKAnisgTmV1ZSBBcHAiLjwvZGl2Pic7cmV0dXJuO30KICBlbC5pbm5lckhUTUw9YXBwcy5tYXAoYT0+YAogICAgPGRpdiBjbGFzcz0iYXBwLWl0ZW0iPgogICAgICA8ZGl2IGNsYXNzPSJhaS1tYWluIj48ZGl2IGNsYXNzPSJhaS1uYW1lIj4ke2VzYyhhLm5hbWUpfTwvZGl2PjxkaXYgY2xhc3M9ImFpLXN1YiI+JHtlc2MoYS5yZXBvKX0gwrcgJHtlc2MoYS5wa2cpfTwvZGl2PjwvZGl2PgogICAgICA8ZGl2IGNsYXNzPSJhaS1hY3QiPgogICAgICAgICR7YS5hcGtVcmw/YDxhIGNsYXNzPSJjaGlwIGRsIiBocmVmPSIke2VzYyhhLmFwa1VybCl9IiBkb3dubG9hZD7irIcgQVBLPC9hPmA6IiJ9CiAgICAgICAgPGJ1dHRvbiBjbGFzcz0iY2hpcCIgZGF0YS11aWQ9IiR7YS51aWR9Ij7DlmZmbmVuPC9idXR0b24+CiAgICAgIDwvZGl2PgogICAgPC9kaXY+YCkuam9pbigiIik7CiAgZWwucXVlcnlTZWxlY3RvckFsbCgiYnV0dG9uW2RhdGEtdWlkXSIpLmZvckVhY2goYj0+Yi5vbmNsaWNrPSgpPT5vcGVuQXBwKGIuZGF0YXNldC51aWQpKTsKfQoKLy8gLS0tLSBFZGl0b3IgLS0tLQpmdW5jdGlvbiBzaG93RWRpdG9yKHRpdGxlLGlzRXhpc3RpbmcpewogICQoImVkaXRvclRpdGxlIikudGV4dENvbnRlbnQ9dGl0bGU7CiAgJCgiZGVsIikuc3R5bGUuZGlzcGxheT1pc0V4aXN0aW5nPyJibG9jayI6Im5vbmUiOwogIGNsZWFyTG9nKCk7JCgiZGwiKS5zdHlsZS5kaXNwbGF5PSJub25lIjskKCJydW5MaW5rIikuc3R5bGUuZGlzcGxheT0ibm9uZSI7CiAgJCgiZWRpdG9yIikuaGlkZGVuPWZhbHNlOyQoImVkaXRvciIpLnNjcm9sbEludG9WaWV3KHtiZWhhdmlvcjoic21vb3RoIn0pOwp9CmZ1bmN0aW9uIGZpbGxFZGl0b3IoYSl7CiAgJCgiYXBwTmFtZSIpLnZhbHVlPWEubmFtZXx8IiI7JCgiYXBwSWQiKS52YWx1ZT1hLnBrZ3x8IiI7JCgiYXBwUmVwbyIpLnZhbHVlPWEucmVwb3x8IiI7CiAgJCgiZmlsZUxhYmVsIikudGV4dENvbnRlbnQ9YS5zY3JpcHQ/KCLwn5OEICIrKGEuc2NyaXB0TmFtZXx8IlNrcmlwdCIpKyIgKGdlbGFkZW4pIik6IvCfk4QgU2tyaXB0IGxhZGVu4oCmIjsKICByZW5kZXJWZXJzaW9ucyhhKTsKfQokKCJuZXdBcHAiKS5vbmNsaWNrPSgpPT57CiAgY3VyPXt1aWQ6ImEiK0RhdGUubm93KCkrTWF0aC5mbG9vcihNYXRoLnJhbmRvbSgpKjEwMDApLG5hbWU6IiIscGtnOiJjb20uZGVpbm5hbWUuYXBwIixyZXBvOiIiLHNjcmlwdE5hbWU6IiIsc2NyaXB0OiIiLGFwa1VybDoiIix2ZXJzaW9uczpbXX07CiAgZmlsbEVkaXRvcihjdXIpO3Nob3dFZGl0b3IoIk5ldWUgQXBwIixmYWxzZSk7Cn07CmZ1bmN0aW9uIG9wZW5BcHAodWlkKXsKICBjdXI9YXBwcy5maW5kKGE9PmEudWlkPT09dWlkKTtpZighY3VyKXJldHVybjsKICBmaWxsRWRpdG9yKGN1cik7c2hvd0VkaXRvcihjdXIubmFtZXx8IkFwcCIsdHJ1ZSk7Cn0KJCgiZmlsZSIpLm9uY2hhbmdlPWU9PnsKICBjb25zdCBmPWUudGFyZ2V0LmZpbGVzWzBdO2lmKCFmfHwhY3VyKXJldHVybjsKICBjb25zdCByPW5ldyBGaWxlUmVhZGVyKCk7CiAgci5vbmxvYWQ9KCk9PntjdXIuc2NyaXB0PXIucmVzdWx0O2N1ci5zY3JpcHROYW1lPWYubmFtZTskKCJmaWxlTGFiZWwiKS50ZXh0Q29udGVudD0i8J+ThCAiK2YubmFtZSsiICgiK01hdGgucm91bmQoZi5zaXplLzEwMjQpKyIga0IpIjt9OwogIHIucmVhZEFzVGV4dChmLCJ1dGYtOCIpOwp9OwpmdW5jdGlvbiByZWFkRWRpdG9yKCl7CiAgaWYoIWN1cilyZXR1cm47CiAgY3VyLm5hbWU9JCgiYXBwTmFtZSIpLnZhbHVlLnRyaW0oKXx8IkFwcCI7CiAgY3VyLnBrZz0oJCgiYXBwSWQiKS52YWx1ZS50cmltKCl8fCJjb20uZGVpbm5hbWUuYXBwIikucmVwbGFjZSgvW15cdy5dL2csIiIpOwogIGN1ci5yZXBvPSgkKCJhcHBSZXBvIikudmFsdWUudHJpbSgpfHxzbHVnKGN1ci5uYW1lKSkucmVwbGFjZSgvW15cdy4tXS9nLCItIik7Cn0KZnVuY3Rpb24gcGVyc2lzdEN1cigpewogIGlmKCFhcHBzLmZpbmQoYT0+YS51aWQ9PT1jdXIudWlkKSlhcHBzLnB1c2goY3VyKTsKICBzYXZlQXBwcygpO3JlbmRlckFwcHMoKTsKfQokKCJzYXZlIikub25jbGljaz0oKT0+e3JlYWRFZGl0b3IoKTtpZighY3VyLnNjcmlwdCl7YWxlcnQoIkJpdHRlIHp1ZXJzdCBlaW4gU2tyaXB0IGxhZGVuLiIpO3JldHVybjt9cGVyc2lzdEN1cigpO2FsZXJ0KCJHZXNwZWljaGVydDogIitjdXIubmFtZSk7b3BlbkFwcChjdXIudWlkKTt9OwokKCJkZWwiKS5vbmNsaWNrPSgpPT57CiAgaWYoIWN1cnx8IWNvbmZpcm0oIkFwcCDigJ4iK2N1ci5uYW1lKyJcIiB3aXJrbGljaCBsw7ZzY2hlbj8gKERhcyBHaXRIdWItUmVwbyBibGVpYnQgYmVzdGVoZW4uKSIpKXJldHVybjsKICBhcHBzPWFwcHMuZmlsdGVyKGE9PmEudWlkIT09Y3VyLnVpZCk7c2F2ZUFwcHMoKTtyZW5kZXJBcHBzKCk7JCgiZWRpdG9yIikuaGlkZGVuPXRydWU7Cn07CgovLyAtLS0tIEdpdEh1Yi1CdWlsZC1IZWxmZXIgKHBybyBSZXBvKSAtLS0tCmFzeW5jIGZ1bmN0aW9uIGVuc3VyZVJlcG8ocmVwbyl7CiAgY29uc3Qgcj1hd2FpdCBnaCgiR0VUIixgL3JlcG9zLyR7Y2ZnLm93bmVyfS8ke3JlcG99YCk7CiAgaWYoci5zdGF0dXM9PT0yMDApcmV0dXJuOwogIGlmKHIuc3RhdHVzPT09NDA0KXsKICAgIGNvbnN0IGM9YXdhaXQgZ2goIlBPU1QiLCIvdXNlci9yZXBvcyIse25hbWU6cmVwbyxwcml2YXRlOmZhbHNlLGF1dG9faW5pdDp0cnVlLGRlc2NyaXB0aW9uOiJBcHAgQnVpbGRlciJ9KTsKICAgIGlmKCFjLm9rKXRocm93IG5ldyBFcnJvcigiUmVwbyBrb25udGUgbmljaHQgZXJzdGVsbHQgd2VyZGVuICgiK2Muc3RhdHVzKyIpIik7CiAgICBhd2FpdCBzbGVlcCgyNTAwKTtyZXR1cm47CiAgfQogIHRocm93IG5ldyBFcnJvcigiUmVwby1QcsO8ZnVuZyBmZWhsZ2VzY2hsYWdlbiAoIityLnN0YXR1cysiKSIpOwp9CmFzeW5jIGZ1bmN0aW9uIHB1dEZpbGUocmVwbyxwYXRoLGNvbnRlbnQsbWVzc2FnZSl7CiAgbGV0IHNoYTtjb25zdCBwPXBhdGguc3BsaXQoIi8iKS5tYXAoZW5jb2RlVVJJQ29tcG9uZW50KS5qb2luKCIvIik7CiAgY29uc3QgZz1hd2FpdCBnaCgiR0VUIixgL3JlcG9zLyR7Y2ZnLm93bmVyfS8ke3JlcG99L2NvbnRlbnRzLyR7cH1gKTsKICBpZihnLnN0YXR1cz09PTIwMCYmZy5kYXRhJiZnLmRhdGEuc2hhKXNoYT1nLmRhdGEuc2hhOwogIGNvbnN0IGJvZHk9e21lc3NhZ2UsY29udGVudDpiNjQoY29udGVudCksYnJhbmNoOiJtYWluIn07aWYoc2hhKWJvZHkuc2hhPXNoYTsKICBjb25zdCByPWF3YWl0IGdoKCJQVVQiLGAvcmVwb3MvJHtjZmcub3duZXJ9LyR7cmVwb30vY29udGVudHMvJHtwfWAsYm9keSk7CiAgaWYoIXIub2spdGhyb3cgbmV3IEVycm9yKCJVcGxvYWQgZmVobGdlc2NobGFnZW46ICIrcGF0aCsiICgiK3Iuc3RhdHVzKyIpIik7Cn0KYXN5bmMgZnVuY3Rpb24gbGF0ZXN0UnVuSWQocmVwbyl7CiAgY29uc3Qgcj1hd2FpdCBnaCgiR0VUIixgL3JlcG9zLyR7Y2ZnLm93bmVyfS8ke3JlcG99L2FjdGlvbnMvcnVucz9wZXJfcGFnZT0xYCk7CiAgY29uc3QgcnVuPXIuZGF0YSYmci5kYXRhLndvcmtmbG93X3J1bnMmJnIuZGF0YS53b3JrZmxvd19ydW5zWzBdO3JldHVybiBydW4/cnVuLmlkOjA7Cn0KYXN5bmMgZnVuY3Rpb24gZGlzcGF0Y2gocmVwbyxpbnB1dHMpewogIGZvcihsZXQgaT0wO2k8ODtpKyspewogICAgY29uc3QgZD1hd2FpdCBnaCgiUE9TVCIsYC9yZXBvcy8ke2NmZy5vd25lcn0vJHtyZXBvfS9hY3Rpb25zL3dvcmtmbG93cy9idWlsZC55bWwvZGlzcGF0Y2hlc2Ase3JlZjoibWFpbiIsaW5wdXRzfSk7CiAgICBpZihkLnN0YXR1cz09PTIwNClyZXR1cm47CiAgICBpZihkLnN0YXR1cz09PTQwNCl7YXdhaXQgc2xlZXAoMzAwMCk7Y29udGludWU7fQogICAgdGhyb3cgbmV3IEVycm9yKCJCdWlsZC1TdGFydCBmZWhsZ2VzY2hsYWdlbiAoIitkLnN0YXR1cysiKSIpOwogIH0KICB0aHJvdyBuZXcgRXJyb3IoIldvcmtmbG93IG5pY2h0IHN0YXJ0YmFyIChUaW1lb3V0KS4iKTsKfQphc3luYyBmdW5jdGlvbiBwb2xsUnVuKHJlcG8scHJldklkKXsKICBjb25zdCBkZWFkbGluZT1EYXRlLm5vdygpKzE4KjYwKjEwMDA7bGV0IHJ1bklkPTA7CiAgd2hpbGUoRGF0ZS5ub3coKTxkZWFkbGluZSl7YXdhaXQgc2xlZXAoNTAwMCk7Y29uc3QgaWQ9YXdhaXQgbGF0ZXN0UnVuSWQocmVwbyk7aWYoaWQmJmlkIT09cHJldklkKXtydW5JZD1pZDticmVhazt9fQogIGlmKCFydW5JZCl0aHJvdyBuZXcgRXJyb3IoIktlaW4gbmV1ZXIgQnVpbGQgZ2VzdGFydGV0LiIpOwogIHdoaWxlKERhdGUubm93KCk8ZGVhZGxpbmUpewogICAgY29uc3Qgcj1hd2FpdCBnaCgiR0VUIixgL3JlcG9zLyR7Y2ZnLm93bmVyfS8ke3JlcG99L2FjdGlvbnMvcnVucy8ke3J1bklkfWApOwogICAgY29uc3QgcnVuPXIuZGF0YTtpZihydW4mJnJ1bi5zdGF0dXM9PT0iY29tcGxldGVkIilyZXR1cm4gcnVuOwogICAgbG9nKCJTdGF0dXM6ICIrKChydW4mJnJ1bi5zdGF0dXMpfHwi4oCmIikpO2F3YWl0IHNsZWVwKDgwMDApOwogIH0KICB0aHJvdyBuZXcgRXJyb3IoIkJ1aWxkLVRpbWVvdXQuIik7Cn0KYXN5bmMgZnVuY3Rpb24gZ2V0UmVsZWFzZUFwayhyZXBvKXsKICBjb25zdCByPWF3YWl0IGdoKCJHRVQiLGAvcmVwb3MvJHtjZmcub3duZXJ9LyR7cmVwb30vcmVsZWFzZXMvbGF0ZXN0YCk7CiAgaWYoci5zdGF0dXMhPT0yMDB8fCFyLmRhdGF8fCFyLmRhdGEuYXNzZXRzKXJldHVybiBudWxsOwogIGNvbnN0IGE9ci5kYXRhLmFzc2V0cy5maW5kKHg9Pi9cLmFwayQvaS50ZXN0KHgubmFtZSkpO3JldHVybiBhP2EuYnJvd3Nlcl9kb3dubG9hZF91cmw6bnVsbDsKfQoKLy8gLS0tLSBCYXVlbiAtLS0tCiQoImJ1aWxkIikub25jbGljaz1hc3luYygpPT57CiAgaWYoIWNmZy5wYXR8fCFjZmcub3duZXIpe2FsZXJ0KCJCaXR0ZSB6dWVyc3QgR2l0SHViIHZlcmJpbmRlbi4iKTtyZXR1cm47fQogIHJlYWRFZGl0b3IoKTsKICBpZighY3VyLnNjcmlwdCl7YWxlcnQoIkJpdHRlIHp1ZXJzdCBlaW4gU2tyaXB0IGxhZGVuLiIpO3JldHVybjt9CiAgcGVyc2lzdEN1cigpOwogICQoImJ1aWxkIikuZGlzYWJsZWQ9dHJ1ZTskKCJidWlsZCIpLnRleHRDb250ZW50PSJCYXVlIOKApiI7CiAgJCgiZGwiKS5zdHlsZS5kaXNwbGF5PSJub25lIjskKCJydW5MaW5rIikuc3R5bGUuZGlzcGxheT0ibm9uZSI7Y2xlYXJMb2coKTsKICBjb25zdCByZXBvPWN1ci5yZXBvOwogIHRyeXsKICAgIGxvZygiUHLDvGZlIFJlcG9zaXRvcnkgIityZXBvKyIg4oCmIik7YXdhaXQgZW5zdXJlUmVwbyhyZXBvKTsKICAgIGxvZygiTGFkZSBXb3JrZmxvdyBob2NoIOKApiIpO2F3YWl0IHB1dEZpbGUocmVwbywiLmdpdGh1Yi93b3JrZmxvd3MvYnVpbGQueW1sIiwkKCJ3ZllhbWwiKS50ZXh0Q29udGVudC5yZXBsYWNlKC9eXG4vLCIiKSwiQXBwIEJ1aWxkZXI6IHdvcmtmbG93Iik7CiAgICBsb2coIkxhZGUgU2tyaXB0IGhvY2gg4oCmIik7YXdhaXQgcHV0RmlsZShyZXBvLCJidWlsZC5weSIsY3VyLnNjcmlwdCwiQXBwIEJ1aWxkZXI6IHNjcmlwdCIpOwogICAgY29uc3QgcHJldj1hd2FpdCBsYXRlc3RSdW5JZChyZXBvKTsKICAgIGxvZygiU3RhcnRlIEJ1aWxkIOKApiIpO2F3YWl0IGRpc3BhdGNoKHJlcG8se2FwcF9pZDpjdXIucGtnLGFwcF9uYW1lOmN1ci5uYW1lfSk7CiAgICBsb2coIldhcnRlIGF1ZiBkZW4gQnVpbGQgKGVpbmlnZSBNaW51dGVuKSDigKYiKTsKICAgIGNvbnN0IHJ1bj1hd2FpdCBwb2xsUnVuKHJlcG8scHJldik7CiAgICAkKCJydW5MaW5rIikuaHJlZj1ydW4uaHRtbF91cmw7JCgicnVuTGluayIpLnN0eWxlLmRpc3BsYXk9ImJsb2NrIjsKICAgIGlmKHJ1bi5jb25jbHVzaW9uPT09InN1Y2Nlc3MiKXsKICAgICAgbG9nKCJCdWlsZCBlcmZvbGdyZWljaCDinJMiLCJvayIpOwogICAgICBjb25zdCB1cmw9YXdhaXQgZ2V0UmVsZWFzZUFwayhyZXBvKTsKICAgICAgaWYodXJsKXsKICAgICAgICBjdXIuYXBrVXJsPXVybDsKICAgICAgICBpZihOQVRJVkUpewogICAgICAgICAgbG9nKCJTcGVpY2hlcmUgQVBLIGxva2FsIOKApiIpOwogICAgICAgICAgdHJ5e2NvbnN0IHY9YXdhaXQgc2F2ZUFwa0xvY2FsbHkoY3VyLHVybCk7aWYodil7Y3VyLnZlcnNpb25zPWN1ci52ZXJzaW9uc3x8W107Y3VyLnZlcnNpb25zLnB1c2godik7bG9nKCJMb2thbCBnZXNwZWljaGVydDogIit2LnBhdGgsIm9rIik7fX0KICAgICAgICAgIGNhdGNoKGUpe2xvZygiTG9rYWwgc3BlaWNoZXJuIGZlaGxnZXNjaGxhZ2VuOiAiKyhlLm1lc3NhZ2V8fGUpLCJlcnIiKTt9CiAgICAgICAgfQogICAgICAgIHNhdmVBcHBzKCk7cmVuZGVyQXBwcygpO3JlbmRlclZlcnNpb25zKGN1cik7CiAgICAgICAgJCgiZGwiKS5ocmVmPXVybDskKCJkbCIpLnN0eWxlLmRpc3BsYXk9ImJsb2NrIjtsb2coIkFQSyBiZXJlaXQuIiwib2siKTsKICAgICAgfSBlbHNlIGxvZygiUmVsZWFzZS9BUEsgbmljaHQgZ2VmdW5kZW4uIExvZyBwcsO8ZmVuLiIsImVyciIpOwogICAgfWVsc2V7bG9nKCJCdWlsZCBmZWhsZ2VzY2hsYWdlbjogIitydW4uY29uY2x1c2lvbiwiZXJyIik7fQogIH1jYXRjaChlKXtsb2coIkZlaGxlcjogIisoZS5tZXNzYWdlfHxlKSwiZXJyIik7fQogICQoImJ1aWxkIikuZGlzYWJsZWQ9ZmFsc2U7JCgiYnVpbGQiKS50ZXh0Q29udGVudD0iQVBLIGJhdWVuIjsKfTsKCi8vIC0tLS0gSW5pdCAtLS0tCmxvYWRBbGwoKTsKaWYoY2ZnLnBhdCkkKCJwYXQiKS52YWx1ZT1jZmcucGF0OwpzZXRDb25uKCEhKGNmZy5wYXQmJmNmZy5vd25lcikpOwp1cGRhdGVGb2xkZXJVSSgpOwpyZW5kZXJBcHBzKCk7Cjwvc2NyaXB0Pgo8L2JvZHk+CjwvaHRtbD4K"

CAP_CONFIG = """import type {{ CapacitorConfig }} from '@capacitor/cli';

const config: CapacitorConfig = {{
  appId: '{app_id}',
  appName: '{app_name}',
  webDir: 'www',
  plugins: {{ CapacitorHttp: {{ enabled: true }} }}
}};

export default config;
"""

MAIN_ACTIVITY_JAVA = """package __APP_ID__;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(SafFolderPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
"""

SAF_PLUGIN_JAVA = """package __APP_ID__;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import androidx.documentfile.provider.DocumentFile;
import androidx.activity.result.ActivityResult;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.ActivityCallback;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.io.OutputStream;

@CapacitorPlugin(name = "SafFolder")
public class SafFolderPlugin extends Plugin {

    @PluginMethod
    public void pickFolder(PluginCall call) {
        Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(call, i, "folderPicked");
    }

    @ActivityCallback
    private void folderPicked(PluginCall call, ActivityResult result) {
        if (call == null) return;
        if (result.getResultCode() != Activity.RESULT_OK || result.getData() == null) {
            call.reject("abgebrochen");
            return;
        }
        Uri uri = result.getData().getData();
        try {
            getContext().getContentResolver().takePersistableUriPermission(uri,
                    Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        } catch (Exception e) { }
        DocumentFile tree = DocumentFile.fromTreeUri(getContext(), uri);
        JSObject ret = new JSObject();
        ret.put("uri", uri.toString());
        ret.put("name", (tree != null && tree.getName() != null) ? tree.getName() : "Ordner");
        call.resolve(ret);
    }

    @PluginMethod
    public void saveToFolder(PluginCall call) {
        String treeUri = call.getString("treeUri");
        String subDir = call.getString("subDir", "");
        String fileName = call.getString("fileName");
        String srcPath = call.getString("srcPath");
        if (treeUri == null || fileName == null || srcPath == null) { call.reject("Parameter fehlen"); return; }
        try {
            Context ctx = getContext();
            DocumentFile tree = DocumentFile.fromTreeUri(ctx, Uri.parse(treeUri));
            if (tree == null || !tree.canWrite()) { call.reject("Ordner nicht beschreibbar"); return; }
            DocumentFile dir = tree;
            if (subDir != null && !subDir.isEmpty()) {
                DocumentFile sub = dir.findFile(subDir);
                if (sub == null || !sub.isDirectory()) sub = dir.createDirectory(subDir);
                if (sub != null) dir = sub;
            }
            DocumentFile existing = dir.findFile(fileName);
            if (existing != null) existing.delete();
            DocumentFile doc = dir.createFile("application/octet-stream", fileName);
            if (doc == null) { call.reject("Datei konnte nicht angelegt werden"); return; }
            String path = srcPath.startsWith("file://") ? Uri.parse(srcPath).getPath() : srcPath;
            InputStream in = new FileInputStream(new File(path));
            OutputStream out = ctx.getContentResolver().openOutputStream(doc.getUri());
            byte[] buf = new byte[8192]; int n;
            while ((n = in.read(buf)) > 0) out.write(buf, 0, n);
            out.flush(); out.close(); in.close();
            JSObject ret = new JSObject();
            ret.put("uri", doc.getUri().toString());
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("Speichern fehlgeschlagen: " + e.getMessage());
        }
    }
}
"""


def place_native(proj, app_id):
    base = proj / "android" / "app" / "src" / "main"
    pkg_dir = None
    for root, _dirs, files in os.walk(base):
        if any(f.startswith("MainActivity.") for f in files):
            pkg_dir = Path(root); break
    if not pkg_dir:
        fail("MainActivity nicht gefunden (ist 'cap add android' gelaufen?).")
    for old in ("MainActivity.java", "MainActivity.kt"):
        p = pkg_dir / old
        if p.exists():
            p.unlink()
    (pkg_dir / "MainActivity.java").write_text(MAIN_ACTIVITY_JAVA.replace("__APP_ID__", app_id), encoding="utf-8")
    (pkg_dir / "SafFolderPlugin.java").write_text(SAF_PLUGIN_JAVA.replace("__APP_ID__", app_id), encoding="utf-8")
    ok("SAF-Plugin + MainActivity geschrieben")
    gradle = proj / "android" / "app" / "build.gradle"
    if gradle.exists():
        txt = gradle.read_text(encoding="utf-8")
        if "androidx.documentfile" not in txt:
            txt = txt.replace("dependencies {",
                              'dependencies {\n    implementation "androidx.documentfile:documentfile:1.0.1"', 1)
            gradle.write_text(txt, encoding="utf-8")
            ok("documentfile-Abhaengigkeit ergaenzt")


# ---- JDK automatisch finden (Android-Studio-JBR) ----
def _jdk_ok(h):
    exe = "java.exe" if IS_WINDOWS else "java"
    try:
        return (h / "bin" / exe).exists()
    except OSError:
        return False


def find_studio_jdk():
    home = Path.home()
    c = []
    if IS_WINDOWS:
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        la = os.environ.get("LOCALAPPDATA", str(home / "AppData" / "Local"))
        for b in (Path(pf) / "Android" / "Android Studio", Path(la) / "Programs" / "Android Studio"):
            c += [b / "jbr", b / "jre"]
    elif platform.system() == "Darwin":
        for a in (Path("/Applications/Android Studio.app"), home / "Applications" / "Android Studio.app"):
            c += [a / "Contents" / "jbr" / "Contents" / "Home"]
    else:
        for b in (Path("/opt/android-studio"), home / "android-studio",
                  Path("/snap/android-studio/current/android-studio")):
            c += [b / "jbr"]
    for x in c:
        if _jdk_ok(x):
            return x
    return None


def configure_java(explicit):
    if explicit:
        h = Path(explicit).expanduser().resolve()
        if not _jdk_ok(h):
            fail("--java-home ungueltig: " + str(h))
    else:
        cur = os.environ.get("JAVA_HOME")
        if cur and _jdk_ok(Path(cur)):
            ok("JAVA_HOME bereits gesetzt: " + cur)
            os.environ["PATH"] = str(Path(cur) / "bin") + os.pathsep + os.environ.get("PATH", "")
            return True
        h = find_studio_jdk()
        if not h:
            warn("Kein JDK gefunden. Fuer --apk Android Studio installieren oder --java-home angeben.")
            return False
    os.environ["JAVA_HOME"] = str(h)
    os.environ["PATH"] = str(h / "bin") + os.pathsep + os.environ.get("PATH", "")
    ok("JAVA_HOME: " + str(h))
    return True


def main():
    ap = argparse.ArgumentParser(description="Baut die App-Builder-App als APK.")
    ap.add_argument("--dir", default="appbuilder")
    ap.add_argument("--app-id", default="com.deinname.appbuilder")
    ap.add_argument("--app-name", default="App Builder")
    ap.add_argument("--apk", action="store_true")
    ap.add_argument("--java-home", default=None)
    a = ap.parse_args()

    proj = Path(a.dir).resolve()
    print(f"\n=== App Builder bauen ===\nProjekt: {proj}\nApp-ID : {a.app_id}\n")

    for t in ("node", "npm", "npx"):
        if not tool(t):
            fail(f"'{t}' fehlt (bitte Node.js 22+ installieren).")

    proj.mkdir(parents=True, exist_ok=True)
    if not (proj / "package.json").exists():
        run([tool("npm"), "init", "-y"], cwd=proj)

    run([tool("npm"), "install", "@capacitor/core", "@capacitor/android",
         "@capacitor/filesystem", "@capacitor/share"], cwd=proj)
    run([tool("npm"), "install", "-D", "@capacitor/cli"], cwd=proj)

    (proj / "capacitor.config.ts").write_text(
        CAP_CONFIG.format(app_id=a.app_id, app_name=a.app_name), encoding="utf-8")

    www = proj / "www"
    www.mkdir(exist_ok=True)
    (www / "index.html").write_bytes(base64.b64decode(INDEX_HTML_B64))
    ok("Builder-Oberflaeche geschrieben (www/index.html)")

    if not (proj / "android").exists():
        run([tool("npx"), "cap", "add", "android"], cwd=proj)
    place_native(proj, a.app_id)
    run([tool("npx"), "cap", "sync"], cwd=proj)

    if a.apk:
        if not configure_java(a.java_home):
            fail("Ohne JDK kann die APK nicht gebaut werden.")
        android = proj / "android"
        gw = android / ("gradlew.bat" if IS_WINDOWS else "gradlew")
        if not gw.exists():
            fail("gradlew nicht gefunden.")
        if not IS_WINDOWS:
            os.chmod(gw, 0o755)
        log("Baue Debug-APK …")
        run([str(gw), "assembleDebug"], cwd=android)
        apk = android / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
        ok("APK: " + str(apk)) if apk.exists() else warn("APK nicht am erwarteten Ort.")

    print("\n\033[32m=== Fertig ===\033[0m")
    print(f"In Android Studio oeffnen:  npx cap open android   (im Ordner {proj.name})")
    print("APK direkt:                 python appbuilder_build.py --apk")


if __name__ == "__main__":
    main()
