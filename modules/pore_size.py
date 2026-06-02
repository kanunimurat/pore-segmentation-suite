# -*- coding: utf-8 -*-
"""
pore_size.py — Image-derived pore-size distribution (MIP-style).

Computes an equivalent-diameter distribution from segmented pores and renders a
mercury-intrusion-porosimetry (MIP)-style inline SVG chart: incremental bars +
cumulative curve on a logarithmic pore-diameter axis (dual y-axis).

Scientific scope: this is a 2D, surface, area-weighted distribution of pore
*bodies* derived from images. It is an analogue to — not a substitute for —
mercury intrusion porosimetry, which probes 3D pore *throats* by intruded volume.
"""
import math
import numpy as np


def pore_size_distribution(kept_props, pixel_scale_mm=0.091, n_bins=12, weight='area'):
    """kept_props: list of skimage regionprops (need .area in pixels).
    weight: 'area' (MIP-like, area-weighted) or 'count' (number-weighted).
    Returns a dict or None if no pores."""
    if not kept_props:
        return None
    scale2 = pixel_scale_mm ** 2
    areas = np.array([p.area * scale2 for p in kept_props], dtype=float)      # mm^2
    diam = 2.0 * np.sqrt(areas / np.pi)                                       # mm (equivalent circle)
    diam = diam[diam > 0]
    if diam.size == 0:
        return None
    dmin = max(float(diam.min()), 1e-3)
    dmax = float(diam.max())
    if dmax <= dmin:
        dmax = dmin * 1.5
    edges = np.logspace(math.log10(dmin), math.log10(dmax), n_bins + 1)
    edges[-1] *= 1.0001                                                       # include the max
    w = areas if weight == 'area' else np.ones_like(areas)
    idx = np.clip(np.digitize(diam, edges) - 1, 0, n_bins - 1)
    inc = np.zeros(n_bins)
    cnt = np.zeros(n_bins, dtype=int)
    for i, b in enumerate(idx):
        inc[b] += w[i]
        cnt[b] += 1
    tot = inc.sum() or 1.0
    inc_pct = inc / tot * 100.0
    cum_pct = np.cumsum(inc_pct)
    centers = np.sqrt(edges[:-1] * edges[1:])
    d50 = float(np.interp(50.0, cum_pct, centers)) if cum_pct[-1] >= 50 else float('nan')
    return dict(diameters_mm=diam, areas_mm2=areas, bin_edges=edges, bin_centers=centers,
                inc_pct=inc_pct, cum_pct=cum_pct, counts=cnt, weight=weight, d50=d50)


def psd_svg(dist, title='Pore size distribution',
            xlabel='Pore size diameter (µm)',
            y_inc='Differential pore area (normalized)', y_cum=None,
            fill=None, edge=None, accent=None, pal=None, W=760, Hh=440):
    # ── tema-duyarlı renkler (Oğuz Ergin "Tantuni Endeksi" sıcak paleti) ──
    P = pal or {}
    ink    = P.get('ink',   '#1f2d3a')
    muted  = P.get('muted', '#5b6876')
    grid   = P.get('grid',  '#eceff3')
    axis   = P.get('axis',  '#334155')
    _fill  = fill   or P.get('fill',   '#FBE3CB')
    _edge  = edge   or P.get('edge',   '#C25A18')
    _acc   = accent or P.get('accent', '#E8722C')
    _res   = P.get('res_shade', '#b9c2cc')
    _resop = P.get('res_op',    '0.28')
    d_um = np.asarray(dist['diameters_mm'], float) * 1000.0           # mm -> µm
    w = np.asarray(dist['areas_mm2'], float) if dist.get('weight','area')=='area' else np.ones_like(d_um)
    d_um = d_um[d_um > 0]
    if d_um.size == 0:
        return '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="40"></svg>'
    logd = np.log10(d_um)
    xlo = math.floor(logd.min()*1 - 0.25); xhi = math.ceil(logd.max()*1 + 0.25)
    if xhi - xlo < 1: xhi = xlo + 1
    wn = w / w.sum()
    mean = float((wn*logd).sum()); var = float((wn*(logd-mean)**2).sum()); sd = math.sqrt(max(var,1e-6))
    h = 0.9 * sd * (len(logd)**(-0.2)) if sd > 0 else 0.15
    h = max(h, 0.08)
    grid_x = np.linspace(xlo, xhi, 240)
    dens = np.zeros_like(grid_x)
    for xi, wi in zip(logd, wn):
        dens += wi*np.exp(-0.5*((grid_x-xi)/h)**2)
    dens /= (dens.max() or 1.0)
    L,R,Tg,Bg = 72,34,70,56
    pw=W-L-R; ph=Hh-Tg-Bg
    def X(lx): return L + (lx-xlo)/(xhi-xlo)*pw
    def Y(v):  return Tg+ph - v*ph
    P2=[f'<svg width="100%" viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" font-family="Inter,Segoe UI,Arial,Helvetica,sans-serif">']
    P2.append(f'<text x="{L}" y="20" font-size="14.5" font-weight="700" fill="{ink}">{title}</text>')
    for t in range(0,6):
        yv=Y(t/5)
        P2.append(f'<line x1="{L}" y1="{yv:.1f}" x2="{L+pw}" y2="{yv:.1f}" stroke="{grid}" stroke-width="1"/>')
    dmin_log=float(np.log10(d_um.min()))
    if dmin_log>xlo:
        xr=X(dmin_log)
        P2.append(f'<rect x="{L:.1f}" y="{Tg}" width="{max(xr-L,0):.1f}" height="{ph}" fill="{_res}" opacity="{_resop}"/>')
        P2.append(f'<line x1="{xr:.1f}" y1="{Tg}" x2="{xr:.1f}" y2="{Tg+ph}" stroke="{muted}" stroke-width="1.3" stroke-dasharray="3,3"/>')
        P2.append(f'<text x="{(L+xr)/2:.1f}" y="{Tg+ph-8:.1f}" font-size="9.5" text-anchor="middle" fill="{muted}" transform="rotate(-90 {(L+xr)/2:.1f} {Tg+ph-8:.1f})">below imaging resolution</text>')
    pts=[f'{X(grid_x[0]):.1f},{Y(0):.1f}']
    pts+=[f'{X(grid_x[i]):.1f},{Y(dens[i]):.1f}' for i in range(len(grid_x))]
    pts.append(f'{X(grid_x[-1]):.1f},{Y(0):.1f}')
    P2.append(f'<polygon points="{" ".join(pts)}" fill="{_fill}" stroke="{_edge}" stroke-width="2.2"/>')
    P2.append(f'<line x1="{L}" y1="{Tg}" x2="{L}" y2="{Tg+ph}" stroke="{axis}" stroke-width="1.3"/>')
    P2.append(f'<line x1="{L}" y1="{Tg+ph}" x2="{L+pw}" y2="{Tg+ph}" stroke="{axis}" stroke-width="1.3"/>')
    for e in range(int(xlo), int(xhi)+1):
        xv=X(e)
        if L-0.5<=xv<=L+pw+0.5:
            P2.append(f'<line x1="{xv:.1f}" y1="{Tg+ph}" x2="{xv:.1f}" y2="{Tg+ph+5}" stroke="{axis}" stroke-width="1.2"/>')
            lab=('%g'%(10.0**e))
            P2.append(f'<text x="{xv:.1f}" y="{Tg+ph+18}" font-size="10" text-anchor="middle" fill="{muted}">{lab}</text>')
        for m in range(2,10):
            xm=X(e+math.log10(m))
            if L<=xm<=L+pw: P2.append(f'<line x1="{xm:.1f}" y1="{Tg+ph}" x2="{xm:.1f}" y2="{Tg+ph+3}" stroke="{grid}" stroke-width="0.8"/>')
    for t in range(0,6):
        yv=Y(t/5)
        P2.append(f'<line x1="{L-4}" y1="{yv:.1f}" x2="{L}" y2="{yv:.1f}" stroke="{axis}"/>')
        P2.append(f'<text x="{L-7}" y="{yv+3:.1f}" font-size="9" text-anchor="end" fill="{muted}">{t/5:.1f}</text>')
    if dist.get('d50')==dist.get('d50'):
        d50=X(math.log10(dist['d50']*1000.0))
        if L<=d50<=L+pw:
            P2.append(f'<line x1="{d50:.1f}" y1="{Tg}" x2="{d50:.1f}" y2="{Tg+ph}" stroke="{_acc}" stroke-width="1.6" stroke-dasharray="5,4"/>')
            P2.append(f'<text x="{d50+5:.1f}" y="{Tg+14}" font-size="10.5" font-weight="700" fill="{_acc}">D50</text>')
    by=Tg-26
    P2.append(f'<line x1="{L}" y1="{by}" x2="{L+pw}" y2="{by}" stroke="{_acc}" stroke-width="2.5"/>')
    bounds=[(-1,'0.1 µm'),(3,'1 mm')]
    for lx,lab in bounds:
        if xlo<lx<xhi:
            xv=X(lx)
            P2.append(f'<line x1="{xv:.1f}" y1="{by-6}" x2="{xv:.1f}" y2="{by+6}" stroke="{_acc}" stroke-width="2.5"/>')
    regions=[(-9,-1,'Sub-capillary'),(-1,3,'Capillary'),(3,9,'Super-capillary')]
    for a,b,name in regions:
        a2=max(a,xlo); b2=min(b,xhi)
        if b2-a2>0.35:
            xc=X((a2+b2)/2)
            P2.append(f'<text x="{xc:.1f}" y="{by-10}" font-size="11" font-weight="700" text-anchor="middle" fill="{_acc}">{name}</text>')
    P2.append(f'<text x="{L+pw/2:.0f}" y="{Hh-8}" font-size="12" text-anchor="middle" fill="{ink}">{xlabel}</text>')
    cy=Tg+ph/2
    P2.append(f'<text x="16" y="{cy:.0f}" font-size="11" text-anchor="middle" fill="{ink}" transform="rotate(-90 16 {cy:.0f})">{y_inc}</text>')
    P2.append('</svg>')
    return ''.join(P2)
