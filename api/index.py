#!/usr/bin/env python3
"""Challan lookup API — Vercel. No source labels in responses."""

from __future__ import annotations

import base64
import re
import secrets
from typing import Dict, List, Optional

import requests
import urllib3
from flask import Flask, jsonify, request

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

_LIST = "https://challan-info-new-abhigyan.vercel.app/challaninfo"
_BASE = "https://echallan.parivahan.nic.in"
_UA = (
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/155.0.0.0 Mobile Safari/537.36"
)


def _upload(img: Optional[bytes], name: str = "photo.jpg") -> Optional[str]:
    if not img:
        return None
    try:
        r = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": (name, img, "image/jpeg")},
            timeout=45,
        )
        url = (r.json().get("data") or {}).get("url") or ""
        m = re.search(r"tmpfiles\.org/(\d+)", url)
        return f"https://tmpfiles.org/dl/{m.group(1)}" if m else (url or None)
    except Exception:
        return None


def _b64_bytes(data_uri: str) -> Optional[bytes]:
    try:
        if data_uri.startswith("data:"):
            data_uri = data_uri.split(",", 1)[1]
        return base64.b64decode(data_uri)
    except Exception:
        return None


def _session() -> requests.Session:
    s = requests.Session()
    s.verify = False
    s.headers.update(
        {
            "User-Agent": _UA,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
            "Origin": _BASE,
            "sec-ch-ua": '"Google Chrome";v="155", "Chromium";v="155", "Not(A:Brand";v="24"',
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": '"Android"',
        }
    )
    for path in ("/challan/challan-services", "/challan/up-traffic-challan"):
        try:
            s.get(
                _BASE + path,
                timeout=25,
                headers={
                    "Accept": "text/html,application/xhtml+xml",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                },
            )
        except Exception:
            pass
    return s


def _raw(challan_no: str) -> dict:
    s = _session()
    r = s.get(
        f"{_BASE}/ecitizen/transcitizen/printClientChallanDetails/v1.0",
        params={"challanNo": challan_no},
        timeout=40,
        headers={
            "Referer": f"{_BASE}/challan/print/up-traffic-challan?challanNo={challan_no}",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        },
    )
    try:
        return r.json()
    except Exception:
        return {"status": "FAILURE", "message": "fetch failed", "http": r.status_code}


def _clean(raw: dict) -> dict:
    if not isinstance(raw, dict):
        return {"ok": False, "error": "bad response"}
    if raw.get("status") == "FAILURE" or (raw.get("message") and not raw.get("result")):
        return {"ok": False, "error": raw.get("message") or "not found"}
    rows = raw.get("result") or []
    if not rows:
        return {"ok": False, "error": "no challan"}

    r0 = rows[0]
    status = r0.get("status") or {}
    vehicle = r0.get("vehicle") or {}
    details = r0.get("challanDetails") or {}
    offences = r0.get("normalOffence") or []
    accused = r0.get("accused") or []
    vcourt = r0.get("vcourt") if isinstance(r0.get("vcourt"), dict) else {}
    circle = (
        r0.get("circleOfficeDetails")
        if isinstance(r0.get("circleOfficeDetails"), dict)
        else {}
    )
    veh_no = vehicle.get("vehicleNo") or status.get("challanDocNo") or ""

    return {
        "ok": True,
        "challanNo": r0.get("challanNo"),
        "challanId": r0.get("id"),
        "challanDate": r0.get("challanDate"),
        "chUploadDt": r0.get("chUploadDt"),
        "stateCd": r0.get("stateCd"),
        "deptType": r0.get("deptType"),
        "offCd": r0.get("offCd"),
        "challanSource": r0.get("challanSource"),
        "challanFor": r0.get("challanFor"),
        "accusedType": r0.get("accusedType"),
        "isActive": r0.get("isActive"),
        "noticeNo": r0.get("noticeNo"),
        "chViolationId": r0.get("chViolationId"),
        "latLong": r0.get("latLong"),
        "amount": status.get("amount"),
        "paymentStatus": status.get("status"),
        "paymentDate": status.get("paymentDate"),
        "receiptNo": status.get("receiptNo"),
        "transactionId": status.get("transactionId"),
        "paymentGateway": status.get("paymentGateway"),
        "isSettled": status.get("isSettled"),
        "acfAmount": status.get("acfAmount"),
        "challanDocNo": status.get("challanDocNo"),
        "vehicleNo": veh_no,
        "vehicleType": vehicle.get("vehicleType"),
        "vehicleClass": vehicle.get("vehicleClass"),
        "vehicleCategory": vehicle.get("vehicleCategory"),
        "chassisNo": vehicle.get("chasisNo") or vehicle.get("chassisNo"),
        "engineNo": vehicle.get("engineNo"),
        "fuel": vehicle.get("fuel"),
        "color": vehicle.get("color"),
        "seatingCap": vehicle.get("seatingCap"),
        "standingCap": vehicle.get("standingCap"),
        "taxUpto": vehicle.get("taxUpto"),
        "financer": vehicle.get("financer"),
        "ownerSrNo": vehicle.get("ownerSrNo"),
        "ownerName": vehicle.get("ownerName"),
        "ownerFatherName": vehicle.get("ownerFatherName"),
        "permanentAddress": vehicle.get("permanentAddress"),
        "presentAddress": vehicle.get("presentAddress"),
        "place": details.get("challanPlace"),
        "remark": details.get("remark"),
        "speedLimit": details.get("speedLimit"),
        "actualSpeed": details.get("actualSpeed"),
        "roadName": details.get("roadName"),
        "itmsCaseId": details.get("itmsCaseId"),
        "itmsChallanSource": details.get("itmsChallanSource"),
        "officerId": r0.get("officerId"),
        "officerName": r0.get("officerName"),
        "officerDesignation": r0.get("officerDesignation"),
        "officerUserName": r0.get("officerUserName"),
        "empId": r0.get("empId"),
        "rtoName": r0.get("rtoName"),
        "courtName": r0.get("courtName"),
        "courtAddress": r0.get("courtAddress"),
        "courtId": vcourt.get("courtId"),
        "hearingDate": vcourt.get("hearingDate"),
        "dispatchNo": vcourt.get("dispatchNo"),
        "isVehicleImpounded": r0.get("isVehicleImpounded"),
        "isDocumentImpounded": r0.get("isDocumentImpounded"),
        "isDlSuspend": r0.get("isDlSuspend"),
        "circleName": circle.get("circleName"),
        "circleAddress": circle.get("circleAddress"),
        "officeName": circle.get("officeName"),
        "districtName": circle.get("districtName"),
        "offences": offences,
        "accused": accused,
        "status_block": status,
        "vehicle_block": vehicle,
        "challanDetails_block": details,
        "vcourt_block": vcourt,
        "circleOfficeDetails_block": circle,
        "impounds": r0.get("impounds") or [],
        "extendedOffence": r0.get("extendedOffence") or [],
        "customOffence": r0.get("customOffence"),
        "_v": veh_no,
        "_img1": details.get("vehicleImg"),
        "_img2": details.get("vehicleImg2"),
        "_img3": details.get("vehicleImg3"),
    }


def _fix_dms(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.search(r"(https://itmschallan\.parivahan\.gov\.in/\S+)", url)
    if m:
        return m.group(1).rstrip('"')
    if url.startswith("http"):
        return url
    return None


def _photos_json(vehicle: str, challan_no: str) -> dict:
    s = _session()
    try:
        r = s.post(
            f"{_BASE}/etrans/internal/get-images",
            json={"challanDocNo": vehicle, "challanNo": challan_no},
            headers={
                "Content-Type": "application/json",
                "X004": "X004",
                "X005": str(secrets.randbelow(9000) + 1000),
                "Referer": f"{_BASE}/challan/up-traffic-challan",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-Mode": "cors",
            },
            timeout=50,
        )
        j = r.json()
        return j if isinstance(j, dict) else {}
    except Exception:
        return {}


def _attach_photos(det: dict) -> dict:
    if not det.get("ok"):
        return det
    challan_no = det.get("challanNo") or ""
    vehicle = det.pop("_v", None) or det.get("vehicleNo") or ""
    imgs = {
        "vehicleImgUrl": det.pop("_img1", None),
        "vehicleImg2": det.pop("_img2", None),
        "vehicleImg3": det.pop("_img3", None),
    }
    out: Dict[str, Optional[str]] = {}

    if vehicle and challan_no:
        data = _photos_json(vehicle, challan_no)
        photos = data.get("data") if isinstance(data, dict) else None
        if isinstance(photos, dict):
            for key in ("photo1", "photo2", "photo3"):
                uri = photos.get(key)
                if not isinstance(uri, str) or len(uri) < 50:
                    continue
                b = _b64_bytes(uri)
                if b:
                    out[key] = _upload(b, f"{challan_no}_{key}.jpg")
        elif isinstance(photos, str) and len(photos) > 50:
            b = _b64_bytes(photos)
            if b:
                out["photo1"] = _upload(b, f"{challan_no}_photo1.jpg")

    for k, u in imgs.items():
        u = _fix_dms(u or "")
        if not u:
            continue
        try:
            s = _session()
            r = s.get(u, timeout=35, headers={"Referer": _BASE + "/"})
            ctype = r.headers.get("Content-Type") or ""
            if r.status_code == 200 and r.content and "html" not in ctype:
                out[k] = _upload(r.content, f"{challan_no}_{k}.jpg")
        except Exception:
            pass

    det["photo_url"] = out.get("photo1") or out.get("vehicleImgUrl")
    det["photos"] = out
    return det


def _detail(challan_no: str, with_photos: bool = True) -> dict:
    det = _clean(_raw(challan_no.strip()))
    if det.get("ok") and with_photos:
        det = _attach_photos(det)
    else:
        det.pop("_v", None)
        det.pop("_img1", None)
        det.pop("_img2", None)
        det.pop("_img3", None)
    return det


def _list_vehicle(veh: str) -> dict:
    r = requests.get(_LIST, params={"vehicle": veh}, timeout=30)
    try:
        data = r.json()
    except Exception:
        return {"ok": False, "error": "list failed"}
    if r.status_code != 200 or not data.get("ok"):
        return {"ok": False, "error": "list failed"}
    return data


def _numbers(data: dict) -> List[str]:
    nums = []
    for key in ("pendingChallans", "paidChallans"):
        for item in data.get(key) or []:
            if isinstance(item, dict) and item.get("challanNumber"):
                nums.append(str(item["challanNumber"]).strip().upper())
    return list(dict.fromkeys(nums))


@app.get("/")
def home():
    return jsonify(
        {
            "ok": True,
            "endpoints": [
                "/vehicletochallaninfo?vehicle=",
                "/challaninfobychallanno?challan=",
            ],
        }
    )


@app.get("/challaninfobychallanno")
def by_challan():
    ch = (request.args.get("challan") or request.args.get("no") or "").strip()
    if len(ch) < 6:
        return jsonify({"ok": False, "error": "challan= required"}), 400
    with_photos = request.args.get("photos", "1") not in ("0", "false", "no")
    result = _detail(ch, with_photos=with_photos)
    return jsonify(result), (200 if result.get("ok") else 502)


@app.get("/vehicletochallaninfo")
def by_vehicle():
    veh = "".join(
        c for c in (request.args.get("vehicle") or "").strip().upper() if c.isalnum()
    )
    if len(veh) < 6:
        return jsonify({"ok": False, "error": "vehicle= required"}), 400

    listed = _list_vehicle(veh)
    if not listed.get("ok"):
        return jsonify({"ok": False, "error": listed.get("error") or "list failed"}), 502

    numbers = _numbers(listed)
    do_full = request.args.get("full", "1") not in ("0", "false", "no")
    if request.args.get("nextgen") in ("0", "false", "no"):
        do_full = False
    with_photos = request.args.get("photos", "1") not in ("0", "false", "no")
    max_detail = int(request.args.get("max") or 5)

    details = []
    if do_full:
        for no in numbers[:max_detail]:
            details.append(_detail(no, with_photos=with_photos))

    return jsonify(
        {
            "ok": True,
            "vehicle": veh,
            "pending_count": listed.get("pending_count"),
            "paid_count": listed.get("paid_count"),
            "pendingChallans": listed.get("pendingChallans") or [],
            "paidChallans": listed.get("paidChallans") or [],
            "challan_numbers": numbers,
            "details": details,
            "details_count": len(details),
        }
    )
