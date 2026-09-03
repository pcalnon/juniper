#!/usr/bin/env python3
"""
Project:      Juniper
Sub-Project:  juniper-ml
Application:  Canopy E2E arc -- modebar + download idiom probe for M-TOPOLOGY-14 (ad-hoc)
Author:       Paul Calnon
Version:      0.1.0
License:      MIT License

PINS TWO UNKNOWNS BEFORE M-TOPOLOGY-14 GETS A SCORER, because guessing either
would produce a row that fails for a reason that has nothing to do with the
product:

  1. WHICH ELEMENT IS THE CAMERA BUTTON. An earlier probe read the modebar as
     ``present: True`` with ``buttons: []`` using ``a.modebar-btn`` -- so either
     that selector is wrong for this plotly build, or the buttons mount lazily on
     hover. This dumps the modebar's real markup instead of assuming.
  2. WHETHER PLAYWRIGHT SEES THE DOWNLOAD AT ALL. plotly's ``toImage`` builds the
     PNG client-side and saves it by clicking a synthetic ``<a download>`` at a
     blob URL. That is not a navigation, so "Playwright will catch it" is an
     assumption, not a fact -- and a scorer built on a wrong assumption reports
     "no download" for a working camera button.

M-TOPOLOGY-14's contract (`network_visualizer.py:462-473`,
`_dynamic_graph_config`): ``format: png``, ``scale: 2``, and
``filename: canopy_network_<YYYYmmdd>_<HHMMSS>``. Note the MOUNT config
(`:245-256`) carries no ``filename`` at all, so a click before the first rebuild
would save plotly's default name -- the timestamped name only exists once the
rebuild has run.

Usage:
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \
        util/ad-hoc/2026-09-03_modebar_download_probe.py

See util/ad-hoc/README.md for the ad-hoc-script convention.
"""

from __future__ import annotations

import importlib.util
import json
import os
import struct
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name: str, fname: str):
    spec = importlib.util.spec_from_file_location(name, os.path.join(_HERE, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_drv = _load("_seg17drv", "e2e_seg17_topology_driver.py")

log = _drv.log
open_dashboard = _drv.open_dashboard
open_tab = _drv.open_tab
wake_topology = _drv.wake_topology
settle_figure = _drv.settle_figure
scroll_graph_into_view = _drv.scroll_graph_into_view
NV = _drv.NV
RUN_DIR = _drv.RUN_DIR

OUT = os.path.join(RUN_DIR, "modebar_download_probe.json")

# Dump the modebar's REAL markup: tag names, classes and every attribute that
# could identify a button, rather than testing one guessed selector.
_JS_MODEBAR = """(id) => {
  const root = document.getElementById(id);
  if (!root) return {present:false};
  const bar = root.querySelector('.modebar');
  if (!bar) return {present:true, bar:false};
  const groups = [...bar.querySelectorAll('.modebar-group')];
  const btns = [...bar.querySelectorAll('*')].filter(e => (e.className || '').toString().indexOf('modebar-btn') >= 0);
  return {
    present: true, bar: true,
    bar_class: (bar.className || '').toString(),
    bar_display: getComputedStyle(bar).display,
    bar_opacity: getComputedStyle(bar).opacity,
    n_groups: groups.length,
    n_btns: btns.length,
    btns: btns.map(b => ({
      tag: b.tagName,
      cls: (b.className || '').toString().slice(0, 60),
      data_title: b.getAttribute('data-title'),
      data_attr: b.getAttribute('data-attr'),
      data_val: b.getAttribute('data-val'),
      rect: (r => ({x: Math.round(r.left + r.width / 2), y: Math.round(r.top + r.height / 2),
                    w: Math.round(r.width), h: Math.round(r.height)}))(b.getBoundingClientRect()),
    })),
    html_head: (bar.innerHTML || '').slice(0, 400),
  };
}"""

_JS_CONFIG = """(id) => {
  const root = document.getElementById(id);
  const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
  if (!gd) return null;
  const c = gd._context || {};
  return {toImageButtonOptions: c.toImageButtonOptions || null,
          displayModeBar: c.displayModeBar,
          w: gd.getBoundingClientRect().width, h: gd.getBoundingClientRect().height};
}"""


def png_size(path: str):
    """(width, height) from the PNG IHDR -- no image library needed.

    Reading the real pixel dimensions is how ``scale: 2`` gets VERIFIED rather
    than trusted: a config that declares scale 2 while rendering at 1 is exactly
    the "config says X, render does Y" class this arc keeps finding.
    """
    with open(path, "rb") as fh:
        head = fh.read(33)
    if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def main() -> int:
    from playwright.sync_api import sync_playwright

    out: dict = {}
    capture: list = []
    with sync_playwright() as pw:
        browser, ctx, page = open_dashboard(pw, capture)
        try:
            open_tab(page, "Network Topology")
            wake = wake_topology(page)
            log(f"wake_topology: {wake}")
            if not wake.get("woke"):
                out["error"] = "graph never painted"
                return 1
            settle_figure(page, budget_s=30)
            scroll_graph_into_view(page)
            gid = f"{NV}-graph"

            out["config"] = page.evaluate(_JS_CONFIG, gid)
            log(f"  graph config: {out['config']}")

            # 1. modebar BEFORE hover, then AFTER -- plotly mounts it on hover by
            #    default, and "buttons: []" may simply mean "not hovered yet".
            out["modebar_before_hover"] = page.evaluate(_JS_MODEBAR, gid)
            log(f"  modebar before hover: bar={out['modebar_before_hover'].get('bar')} n_btns={out['modebar_before_hover'].get('n_btns')} display={out['modebar_before_hover'].get('bar_display')} opacity={out['modebar_before_hover'].get('bar_opacity')}")

            box = page.evaluate("(id) => { const r = document.getElementById(id).getBoundingClientRect(); return {x: r.left + r.width/2, y: r.top + r.height/2}; }", gid)
            page.mouse.move(box["x"], box["y"])
            page.wait_for_timeout(1200)
            mb = page.evaluate(_JS_MODEBAR, gid)
            out["modebar_after_hover"] = mb
            log(f"  modebar after hover : bar={mb.get('bar')} n_btns={mb.get('n_btns')} display={mb.get('bar_display')} opacity={mb.get('bar_opacity')}")
            for b in (mb.get("btns") or [])[:14]:
                log(f"    {b['tag']:4s} data-title={str(b['data_title'])[:34]:36s} data-attr={str(b['data_attr'])[:16]:18s} rect={b['rect']}")
            if not mb.get("btns"):
                log(f"    !! no buttons matched; raw modebar html head: {mb.get('html_head')!r}")

            # 2. the camera button, found by data-title rather than position.
            cam = next((b for b in (mb.get("btns") or []) if "png" in str(b.get("data_title", "")).lower() or str(b.get("data_attr")) == "toImage"), None)
            out["camera_button"] = cam
            log(f"  camera button: {cam}")
            if not cam:
                out["error"] = "no camera/toImage button found in the modebar"
                log("  !! cannot pin M-TOPOLOGY-14's idiom without it")
                return 1

            # 3. DOES PLAYWRIGHT SEE THE DOWNLOAD? plotly saves via a synthetic
            #    <a download> at a blob URL, which is not a navigation.
            dest = os.path.join(RUN_DIR, "m14_download")
            os.makedirs(dest, exist_ok=True)
            got = {}
            # SPLIT THE QUESTION, same as every other gesture in this arc. "No
            # download" has two causes with different fixes: plotly never got as far
            # as saving (its toImage render failed or is still running -- this figure
            # is 1891 traces and scale 2 means a ~2204x1200 raster), or it saved and
            # Playwright did not surface it as a download event. Hooking
            # createObjectURL and the anchor click separates them.
            page.evaluate(
                """() => {
                     window.__m14 = {objurls: 0, anchor_clicks: 0, downloads: [], errors: []};
                     const origCreate = URL.createObjectURL.bind(URL);
                     URL.createObjectURL = (b) => { window.__m14.objurls++; return origCreate(b); };
                     const origClick = HTMLAnchorElement.prototype.click;
                     HTMLAnchorElement.prototype.click = function () {
                       window.__m14.anchor_clicks++;
                       if (this.hasAttribute('download')) {
                         window.__m14.downloads.push({name: this.getAttribute('download'),
                                                      href_scheme: (this.href || '').split(':')[0]});
                       }
                       return origClick.apply(this, arguments);
                     };
                     window.addEventListener('error', (e) => window.__m14.errors.push(String(e.message).slice(0,200)));
                   }"""
            )
            try:
                # 120 s, not 30: rendering 1891 traces at scale 2 is not quick, and a
                # timeout that is merely too short reads identically to "never saved".
                with page.expect_download(timeout=120000) as dl_info:
                    page.mouse.click(cam["rect"]["x"], cam["rect"]["y"])
                dl = dl_info.value
                saved = os.path.join(dest, dl.suggested_filename)
                dl.save_as(saved)
                got = {"caught": True, "suggested_filename": dl.suggested_filename, "saved": saved,
                       "bytes": os.path.getsize(saved), "png_size": png_size(saved)}
            except Exception as e:  # noqa: BLE001
                got = {"caught": False, "why": f"{type(e).__name__}: {e}"[:200]}
            # Whatever happened, report what the PAGE did -- that is what says
            # whether the button worked and Playwright missed it, or the button
            # never produced a save at all.
            got["page_side"] = page.evaluate("() => window.__m14 || null")
            out["download"] = got
            log(f"  download caught: {got.get('caught')}  page-side: {got.get('page_side')}")
            if not got.get("caught"):
                ps = got.get("page_side") or {}
                if ps.get("downloads"):
                    log("  !! plotly DID save (an <a download> was clicked) but Playwright saw no download event")
                    log("     -> the idiom is the INTERCEPT, not the button; score on the page-side signal instead")
                elif ps.get("objurls"):
                    log("  !! an object URL was created but no <a download> click followed -- the save path aborted")
                else:
                    log("  !! plotly never got as far as creating an object URL -- toImage failed or is still rendering")
                log(f"     why: {got.get('why')}")
            if got.get("caught"):
                w, h = (got.get("png_size") or (0, 0))
                cw, ch = out["config"]["w"], out["config"]["h"]
                log(f"    graph css size {cw:.0f}x{ch:.0f}  ->  png {w}x{h}  (scale ~{(w / cw) if cw else 0:.2f})")
            # 4. IS IT THE RENDER OR THE SAVE? `Plotly.toImage` is the same
            #    rasteriser the camera button uses, minus the download plumbing.
            #    If it resolves, the image is producible at scale 2 and only the
            #    SAVE path is at fault -- which decides what M-TOPOLOGY-14 can
            #    honestly assert.
            try:
                shot_res = page.evaluate(
                    """async (id) => {
                         const root = document.getElementById(id);
                         const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                         if (!gd || !window.Plotly || !window.Plotly.toImage) return {ok:false, why:'no Plotly.toImage'};
                         const t0 = performance.now();
                         try {
                           const uri = await window.Plotly.toImage(gd, {format:'png', scale:2});
                           return {ok:true, ms: Math.round(performance.now()-t0), len: uri.length,
                                   head: uri.slice(0, 32)};
                         } catch (e) { return {ok:false, ms: Math.round(performance.now()-t0), why: String(e).slice(0,200)}; }
                       }""",
                    gid,
                )
            except Exception as e:  # noqa: BLE001
                shot_res = {"ok": False, "why": f"{type(e).__name__}: {e}"[:200]}
            out["toImage"] = shot_res
            log(f"  Plotly.toImage(scale=2): {shot_res}")
            if shot_res.get("ok"):
                log("     -> the RASTERISER works; only the download/save path is unreachable from the driver")

            # 5. IF THE RASTERISER FAILED: is it this FIGURE, this SCALE, or this
            #    BROWSER? A headless-only limitation is not a product defect, and
            #    filing one as the other is the mistake this arc keeps catching.
            #    Vary one thing at a time: scale, format, and the figure itself.
            if not shot_res.get("ok"):
                matrix = page.evaluate(
                    """async (id) => {
                         const root = document.getElementById(id);
                         const gd = root.classList.contains('js-plotly-plot') ? root : root.querySelector('.js-plotly-plot');
                         const others = [...document.querySelectorAll('.js-plotly-plot')].filter(e => e !== gd);
                         const small = others.length ? others[0] : null;
                         const run = async (target, opts, label) => {
                           if (!target) return {label: label, ok:false, why:'no such graph'};
                           const t0 = performance.now();
                           try { const u = await window.Plotly.toImage(target, opts);
                                 return {label: label, ok:true, ms: Math.round(performance.now()-t0), len: u.length}; }
                           catch (e) { return {label: label, ok:false, ms: Math.round(performance.now()-t0), why: String(e).slice(0,120)}; }
                         };
                         const out = [];
                         out.push(await run(gd, {format:'png', scale:1}, 'topology png scale=1'));
                         out.push(await run(gd, {format:'svg'},          'topology svg'));
                         out.push(await run(small, {format:'png', scale:2}, 'OTHER graph png scale=2'));
                         return {n_other_graphs: others.length,
                                 other_traces: small && small.data ? small.data.length : null,
                                 topo_traces: gd && gd.data ? gd.data.length : null,
                                 results: out};
                       }""",
                    gid,
                )
                out["toImage_matrix"] = matrix
                log(f"  isolation matrix (topology has {matrix.get('topo_traces')} traces; other graph has {matrix.get('other_traces')}):")
                for r in matrix.get("results") or []:
                    log(f"    {r['label']:26s} ok={str(r['ok']):5s} ms={r.get('ms')} {('why=' + str(r.get('why'))) if not r['ok'] else 'len=' + str(r.get('len'))}")
                # THE CONTROL THAT SETTLES IT. plotly's PNG path is
                # SVG -> Blob -> <img> -> canvas -> toDataURL. Run that exact path
                # on a 10x10 hand-made rectangle: nothing about it depends on
                # plotly, the figure, or its size. If even THIS fails, the browser
                # cannot rasterise SVG and no amount of product change would help --
                # which is the difference between a finding and an environment note.
                # TWO controls, differing ONLY in the URL SCHEME.
                #
                # The first version of this control used a blob: URL -- the same
                # scheme plotly uses -- so it shared the mechanism under test and
                # "proved" a browser limitation that does not exist. The page's CSP
                # is `img-src 'self' data:`, which permits data: and OMITS blob:.
                # Varying just the scheme is what separates "this browser cannot
                # rasterise SVG" from "this PAGE forbids blob: images".
                out["svg_raster_control"] = page.evaluate(
                    """async () => {
                         const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
                                   + '<rect width="10" height="10" fill="red"/></svg>';
                         const load = async (url) => {
                           const img = new Image();
                           await new Promise((res, rej) => {
                             img.onload = res;
                             img.onerror = () => rej(new Error('img.onerror'));
                             setTimeout(() => rej(new Error('img load timeout')), 8000);
                             img.src = url;
                           });
                           const c = document.createElement('canvas');
                           c.width = 10; c.height = 10;
                           c.getContext('2d').drawImage(img, 0, 0);
                           return c.toDataURL('image/png').length;
                         };
                         const out = {};
                         const burl = URL.createObjectURL(new Blob([svg], {type: 'image/svg+xml'}));
                         try { out.blob = {ok: true, len: await load(burl)}; }
                         catch (e) { out.blob = {ok: false, why: String(e.message).slice(0,80)}; }
                         finally { URL.revokeObjectURL(burl); }
                         const durl = 'data:image/svg+xml;base64,' + btoa(svg);
                         try { out.data = {ok: true, len: await load(durl)}; }
                         catch (e) { out.data = {ok: false, why: String(e.message).slice(0,80)}; }
                         out.csp = (document.querySelector('meta[http-equiv="Content-Security-Policy"]') || {}).content || '<header-only>';
                         return out;
                       }"""
                )
                ctrl = out["svg_raster_control"]
                log(f"    {'10x10 SVG via blob: URL':26s} ok={str(ctrl.get('blob', {}).get('ok')):5s} {ctrl.get('blob', {}).get('why') or ('len=' + str(ctrl.get('blob', {}).get('len')))}")
                log(f"    {'10x10 SVG via data: URL':26s} ok={str(ctrl.get('data', {}).get('ok')):5s} {ctrl.get('data', {}).get('why') or ('len=' + str(ctrl.get('data', {}).get('len')))}")
                blob_ok = bool(ctrl.get("blob", {}).get("ok"))
                data_ok = bool(ctrl.get("data", {}).get("ok"))
                if data_ok and not blob_ok:
                    log("     -> THE SCHEME IS THE DIFFERENCE. data: rasterises, blob: does not. The page's CSP is")
                    log("        `img-src 'self' data:` — blob: is OMITTED, so plotly's PNG export is blocked BY CANOPY.")
                    log("        This is a PRODUCT defect and affects every user in every browser, not a headless quirk.")
                elif not data_ok and not blob_ok:
                    log("     -> neither scheme rasterises: this really is a browser/environment limitation.")
                else:
                    log("     -> blob: rasterises fine, so the CSP is not the blocker; look elsewhere.")

                # NOTE: the "OTHER graph" row is a WEAK control and is no longer
                # interpreted. It picked whatever second `.js-plotly-plot` existed,
                # which had 0 traces, and its failure is explained by the same CSP
                # block as everything else here. The scheme comparison above is the
                # control that actually discriminates; drawing a conclusion from a
                # 0-trace figure is how the earlier "headless limitation" reading
                # got made.
        finally:
            os.makedirs(RUN_DIR, exist_ok=True)
            with open(OUT, "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=2, default=str)
            log(f"probe -> {OUT}")
            browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
