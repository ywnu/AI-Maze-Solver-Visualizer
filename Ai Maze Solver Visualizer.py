import pygame
import random
import heapq
import math
import time
from collections import deque

# ─────────────────────────────────────────────
#  Layout constants
# ─────────────────────────────────────────────
CELL_SIZE   = 22
GRID_ROWS   = 27
GRID_COLS   = 33
SIDEBAR_W   = 460
TOP_H       = 105
BOTTOM_H    = 46
PAD         = 12
GRID_W      = GRID_COLS * CELL_SIZE
GRID_H      = GRID_ROWS * CELL_SIZE
WIDTH       = GRID_W + SIDEBAR_W + PAD * 3
HEIGHT      = TOP_H + GRID_H + BOTTOM_H + PAD * 2 +60
FPS         = 60

# ─────────────────────────────────────────────
#  Vaporwave palette
# ─────────────────────────────────────────────
BG          = (15,   5,  25)
BG_PANEL    = (22,   8,  38)
BG_CARD     = (30,  10,  50)
BG_HEADER   = (55,  10,  75)
WALL        = (44,  16,  64)
OPEN        = (100, 65, 140)
COL_EXPL    = (255,   0, 255)
COL_PATH    = (0,   255, 255)
COL_START   = (255, 170, 210)
COL_GOAL    = (255, 235,  90)
WHITE       = (255, 255, 255)
DIM         = (160,  80, 190)

ACOL = {
    'DFS':    (0,   230, 255),
    'BFS':    (255,  40, 220),
    'A*':     (255, 230,  50),
    'GREEDY': (255, 140, 200),
}

ALGO_FULL = {
    'DFS':    'DEPTH-FIRST SEARCH',
    'BFS':    'BREADTH-FIRST SEARCH',
    'A*':     'A-STAR SEARCH',
    'GREEDY': 'GREEDY BEST-FIRST SEARCH',
}

ALGO_OPTIMAL = {'DFS': False, 'BFS': True, 'A*': True, 'GREEDY': False}
ALGO_ORDER   = ['DFS', 'BFS', 'A*', 'GREEDY']

# ─────────────────────────────────────────────
#  Font cache
# ─────────────────────────────────────────────
_fc = {}
def F(size, bold=False):
    k = (size, bold)
    if k not in _fc:
        _fc[k] = pygame.font.SysFont('consolas', size, bold=bold)
    return _fc[k]

# ─────────────────────────────────────────────
#  Maze helpers
# ─────────────────────────────────────────────
def generate_maze(rows, cols):
    m = [[1]*cols for _ in range(rows)]
    def ok(r,c): return 0<=r<rows and 0<=c<cols
    m[1][1] = 0
    stk = [(1,1)]
    while stk:
        r,c = stk[-1]
        nb = [(r+dr,c+dc,r+dr//2,c+dc//2)
              for dr,dc in [(-2,0),(2,0),(0,-2),(0,2)]
              if ok(r+dr,c+dc) and m[r+dr][c+dc]==1]
        if nb:
            nr,nc,wr,wc = random.choice(nb)
            m[wr][wc] = m[nr][nc] = 0
            stk.append((nr,nc))
        else:
            stk.pop()
    return m

def nbrs(pos, maze):
    r,c = pos
    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
        nr,nc = r+dr,c+dc
        if 0<=nr<len(maze) and 0<=nc<len(maze[0]) and maze[nr][nc]==0:
            yield (nr,nc)

def h(a,b): return abs(a[0]-b[0])+abs(a[1]-b[1])

def rebuild(cf, s, g):
    if g not in cf and g!=s: return []
    p,cur = [g],g
    while cur!=s: cur=cf[cur]; p.append(cur)
    return p[::-1]

def solve_dfs(maze,s,g):
    stk,cf,vis,ord_ = [s],{},set(),[]
    while stk:
        c=stk.pop()
        if c in vis: continue
        vis.add(c); ord_.append(c)
        if c==g: return rebuild(cf,s,g),ord_
        for n in nbrs(c,maze):
            if n not in vis: cf[n]=c; stk.append(n)
    return [],ord_

def solve_bfs(maze,s,g):
    q,cf,vis,ord_ = deque([s]),{},{s},[]
    while q:
        c=q.popleft(); ord_.append(c)
        if c==g: return rebuild(cf,s,g),ord_
        for n in nbrs(c,maze):
            if n not in vis: vis.add(n);cf[n]=c;q.append(n)
    return [],ord_

def solve_greedy(maze,s,g):
    pq,cf,vis,ord_ = [],{},set(),[]
    heapq.heappush(pq,(h(s,g),s))
    while pq:
        _,c=heapq.heappop(pq)
        if c in vis: continue
        vis.add(c); ord_.append(c)
        if c==g: return rebuild(cf,s,g),ord_
        for n in nbrs(c,maze):
            if n not in vis:
                if n not in cf: cf[n]=c
                heapq.heappush(pq,(h(n,g),n))
    return [],ord_

def solve_astar(maze,s,g):
    pq,cf,gs,vis,ord_ = [],{},{s:0},set(),[]
    heapq.heappush(pq,(0,s))
    while pq:
        _,c=heapq.heappop(pq)
        if c in vis: continue
        vis.add(c); ord_.append(c)
        if c==g: return rebuild(cf,s,g),ord_
        for n in nbrs(c,maze):
            tg=gs[c]+1
            if n not in gs or tg<gs[n]:
                gs[n]=tg; cf[n]=c
                heapq.heappush(pq,(tg+h(n,g),n))
    return [],ord_

SOLVERS = {'DFS':solve_dfs,'BFS':solve_bfs,'A*':solve_astar,'GREEDY':solve_greedy}

# ─────────────────────────────────────────────
#  Drawing helpers
# ─────────────────────────────────────────────
def lc(a,b,t):
    return tuple(max(0,min(255,int(a[i]+(b[i]-a[i])*t))) for i in range(3))

def rr(surf,col,rect,r=8,bw=0,bc=None):
    pygame.draw.rect(surf,col,rect,border_radius=r)
    if bw and bc:
        pygame.draw.rect(surf,bc,rect,bw,border_radius=r)

def glow(surf,rect,col,layers=4,alpha=35,r=10):
    for i in range(layers,0,-1):
        s=pygame.Surface((rect.w+i*8,rect.h+i*8),pygame.SRCALPHA)
        a=int(alpha*(i/layers)**1.6)
        pygame.draw.rect(s,(*col,a),s.get_rect(),border_radius=r+i*3)
        surf.blit(s,(rect.x-i*4,rect.y-i*4))

def T(surf,t,fn,col,pos,anchor='topleft'):
    s=fn.render(t,True,col)
    r_=s.get_rect(**{anchor:pos})
    surf.blit(s,r_); return r_

def pbar(surf,rect,val,mx,col,bg=BG_CARD,r=5):
    rr(surf,bg,rect,r)
    if mx>0:
        w=max(0,int(rect.w*min(val/mx,1.0)))
        if w>0: rr(surf,col,pygame.Rect(rect.x,rect.y,w,rect.h),r)

# ─────────────────────────────────────────────
#  Background
# ─────────────────────────────────────────────
_bg = None
def build_bg():
    global _bg
    _bg=pygame.Surface((WIDTH,HEIGHT))
    _bg.fill(BG)
    for x in range(0,WIDTH,36):
        pygame.draw.line(_bg,(28,9,44),(x,0),(x,HEIGHT))
    for y in range(0,HEIGHT,36):
        pygame.draw.line(_bg,(28,9,44),(0,y),(WIDTH,y))

def draw_bg(surf):
    surf.blit(_bg,(0,0))
    sl=pygame.Surface((WIDTH,1),pygame.SRCALPHA)
    sl.fill((255,255,255,5))
    for y in range(0,HEIGHT,6):
        surf.blit(sl,(0,y))

# ─────────────────────────────────────────────
#  Header
# ─────────────────────────────────────────────
def draw_header(surf,frame,cur_algo):
    ac=ACOL[cur_algo]
    rr(surf,BG_HEADER,pygame.Rect(0,0,WIDTH,TOP_H))
    pygame.draw.line(surf,(255,0,255),(0,2),(WIDTH,2),3)
    pygame.draw.line(surf,(0,255,255),(0,5),(WIDTH,5),1)
    pygame.draw.line(surf,ac,(0,TOP_H-4),(WIDTH,TOP_H-4),3)
    pygame.draw.line(surf,(0,255,255),(0,TOP_H-1),(WIDTH,TOP_H-1),1)
    T(surf,'A PERFORMANCE COMPARISON OF AI SEARCH ALGORITHMS',
      F(15,True),(200,120,230),(WIDTH//2,12),anchor='midtop')
    tc=WHITE if (frame//20)%2==0 else COL_START
    T(surf,'AI Maze Solver Visualizer',F(56,True),tc,(WIDTH//2,28),anchor='midtop')

# ─────────────────────────────────────────────
#  Maze
# ─────────────────────────────────────────────
def draw_maze(surf,maze,start,goal,explored,path,frame,ox,oy):
    fr=pygame.Rect(ox-6,oy-6,GRID_W+12,GRID_H+12)
    glow(surf,fr,(0,255,255),layers=4,alpha=28)
    rr(surf,(0,180,180),fr,r=8,bw=2,bc=(0,255,255))

    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            col=OPEN if maze[r][c]==0 else WALL
            pygame.draw.rect(surf,col,(ox+c*CELL_SIZE,oy+r*CELL_SIZE,CELL_SIZE,CELL_SIZE))

    n=len(explored)
    for idx,(r,c) in enumerate(explored):
        age=n-idx
        fade=max(0.18,1.0-age/max(n,1)*0.72)
        col=lc((90,0,90),COL_EXPL,fade)
        p=max(1,int((1-fade)*4))
        pygame.draw.rect(surf,col,(ox+c*CELL_SIZE+p,oy+r*CELL_SIZE+p,CELL_SIZE-p*2,CELL_SIZE-p*2))

    for idx,(r,c) in enumerate(path):
        col=COL_PATH
        p=2
        pygame.draw.rect(surf,col,(ox+c*CELL_SIZE+p,oy+r*CELL_SIZE+p,CELL_SIZE-p*2,CELL_SIZE-p*2))
        cx_=ox+c*CELL_SIZE+CELL_SIZE//2; cy_=oy+r*CELL_SIZE+CELL_SIZE//2

    def marker(pos,col,label,fn):
        r,c=pos; x=ox+c*CELL_SIZE; y=oy+r*CELL_SIZE
        pulse=0.6+0.35*fn(frame*0.1)
        p=max(1,int(3*(1-pulse)))
        rr(surf,col,pygame.Rect(x+p,y+p,CELL_SIZE-p*2,CELL_SIZE-p*2),r=3)
        T(surf,label,F(10,True),BG,(x+CELL_SIZE//2,y+CELL_SIZE//2),anchor='center')

    marker(start,COL_START,'S',math.sin)
    marker(goal, COL_GOAL, 'G',math.cos)

# ─────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────
def draw_sidebar(surf,cur_algo,explored_now,path_now,
                 all_orders,all_paths,elapsed,frame,
                 completed,speed,cur_idx):

    px=GRID_W+PAD*2+PAD; py=TOP_H+PAD
    pw=SIDEBAR_W-PAD*2;  ph=HEIGHT-TOP_H-BOTTOM_H-PAD*2

    panel=pygame.Rect(px,py,pw,ph)
    rr(surf,BG_PANEL,panel,r=12)
    glow(surf,panel,ACOL[cur_algo],layers=3,alpha=16)
    rr(surf,BG_PANEL,panel,r=12,bw=2,bc=ACOL[cur_algo])

    y=py+8
    T(surf,'>> LIVE ALGORITHM COMPARISON',F(12,True),DIM,(px+14,y))
    y+=18

    # ── 4 algo cards — fixed height so everything fits ─
    # Available vertical space: ph minus header(26) speed(46) selector(78) controls(88) divider(16)
    cards_total = ph - 26 - 46 - 78 - 88 - 16
    card_gap    = 10
    card_h      = 92  # evenly divide remaining space

    for i,aname in enumerate(ALGO_ORDER):
        ac=ACOL[aname]
        cx=px+8; cy=y; cw=pw-16
        card=pygame.Rect(cx,cy,cw,card_h)
        is_cur=(aname==cur_algo)
        is_done=(aname in completed)

        fill=lc(BG_CARD,(ac[0]//5,ac[1]//5,ac[2]//5),0.6) if is_cur else BG_CARD
        rr(surf,fill,card,r=8)
        if is_cur: glow(surf,card,ac,layers=2,alpha=20)
        rr(surf,fill,card,r=8,bw=2 if is_cur else 1,bc=ac)

        # Title row — algo name + full name on same line
        name_surf=F(20,True).render(aname,True,ac)
        surf.blit(name_surf,(cx+10,cy+6))
        full_x=cx+10+name_surf.get_width()+7
        T(surf,f'({ALGO_FULL[aname]})',F(11,True),lc(ac,WHITE,0.35),(full_x,cy+10))

        # Stats
        if is_cur:
            ev=len(explored_now); pv=len(path_now)
            tv=f'{elapsed:.0f}s'
            eff=f'{int(100*pv/max(len(all_orders[i]),1))}%'
            opt='(optimal) ' if ALGO_OPTIMAL[aname] and pv>0 else ''
        elif is_done:
            ev=len(all_orders[i]); pv=len(all_paths[i])
            tv='done'
            eff=f'{int(100*pv/max(ev,1))}%'
            opt='(optimal) ' if ALGO_OPTIMAL[aname] and pv>0 else ''
        else:
            ev=pv=0; tv='--'; eff='--'; opt=''

        sc=(210,210,210)
        row1_y = cy+32
        row2_y = cy+50
        T(surf,f'CELLS EXPLORED: {ev}',   F(11),sc, (cx+10,row1_y))
        T(surf,f'TIME ELAPSED: {tv}',     F(11),sc, (cx+cw-10,row1_y),anchor='topright')
        T(surf,f'PATH LENGTH: {opt}{pv}', F(11),sc, (cx+10,row2_y))
        T(surf,'EFFICIENCY',              F(10),DIM,(cx+cw-78,row2_y))
        T(surf,eff,F(17,True),lc(ac,WHITE,0.45),(cx+cw-10,row2_y+14),anchor='topright')

        # progress bar flush at bottom of card
        progress = min(ev / max(len(all_orders[i]), 1), 1.0)

        pbar(
            surf,
            pygame.Rect(cx + 10, cy + card_h - 8, cw - 20, 5),
            progress,
            1,
            ac,
            bg=lc(BG_CARD, BG, 0.5),
            r=3
        )

        y+=card_h+card_gap

    y+=8

    # ── speed slider ──────────────────────────
    pygame.draw.line(surf,(55,22,80),(px+10,y),(px+pw-10,y),1)
    y+=8
    T(surf,'>> SPEED',F(12,True),DIM,(px+14,y))
    T(surf,f'{speed:.1f}x',F(13,True),WHITE,(px+pw-14,y),anchor='topright')
    y+=18
    track=pygame.Rect(px+14,y,pw-28,7)
    rr(surf,(38,15,55),track,r=4)
    # filled portion
    fill_w=int((pw-28)*(speed-0.5)/9.5)
    rr(surf,lc(ACOL[cur_algo],(80,30,100),0.5),
       pygame.Rect(px+14,y,fill_w,7),r=4)
    kx=px+14+fill_w
    glow(surf,pygame.Rect(kx-7,y-4,14,15),ACOL[cur_algo],layers=2,alpha=50)
    rr(surf,ACOL[cur_algo],pygame.Rect(kx-7,y-4,14,15),r=5)
    y+=22

    # ── algo selector buttons ─────────────────
    pygame.draw.line(surf,(55,22,80),(px+10,y),(px+pw-10,y),1)
    y+=8
    T(surf,'>> ALGORITHM SELECTOR',F(12,True),DIM,(px+14,y))
    y+=16
    # 4 equal buttons across full width
    gap_=4
    bw_=(pw-16-gap_*3)//4
    bh_=52
    # icon drawn with pygame shapes instead of unicode
    for i,aname in enumerate(ALGO_ORDER):
        ac=ACOL[aname]
        bx=px+8+i*(bw_+gap_); by=y
        b=pygame.Rect(bx,by,bw_,bh_)
        is_cur=(aname==cur_algo)
        fill=lc(BG_CARD,ac,0.18) if is_cur else BG_CARD
        rr(surf,fill,b,r=8)
        if is_cur: glow(surf,b,ac,layers=2,alpha=26)
        rr(surf,fill,b,r=8,bw=2 if is_cur else 1,bc=ac)
        # Draw a small shape icon per algo using pygame primitives
        icx=bx+bw_//2; icy=by+15
        if aname=='DFS':   # diamond
            pts=[(icx,icy-8),(icx+8,icy),(icx,icy+8),(icx-8,icy)]
            pygame.draw.polygon(surf,ac,pts); pygame.draw.polygon(surf,BG,pts,1)
        elif aname=='BFS': # concentric squares
            pygame.draw.rect(surf,ac,(icx-8,icy-8,16,16),2)
            pygame.draw.rect(surf,ac,(icx-4,icy-4,8,8),2)
        elif aname=='A*':  # star (4 lines)
            for ang in [0,45,90,135]:
                rad=math.radians(ang)
                pygame.draw.line(surf,ac,
                    (int(icx-8*math.cos(rad)),int(icy-8*math.sin(rad))),
                    (int(icx+8*math.cos(rad)),int(icy+8*math.sin(rad))),2)
        else:              # hexagon outline
            pts=[(int(icx+8*math.cos(math.radians(a))),
                  int(icy+8*math.sin(math.radians(a)))) for a in range(0,360,60)]
            pygame.draw.polygon(surf,ac,pts,2)
        T(surf,aname,F(12,True),ac,(bx+bw_//2,by+28),anchor='midtop')
    y+=bh_+8

    # ── controls ──────────────────────────────
    pygame.draw.line(surf,(55,22,80),(px+10,y),(px+pw-10,y),1)
    y+=8
    T(surf,'>> CONTROLS',F(12,True),DIM,(px+14,y))
    y+=16
    pairs=[('[N]','NEXT',       '[SPACE]','AUTO/PAUSE'),
           ('[+]','FASTER',     '[-]',    'SLOWER'),
           ('[R]','NEW MAZE',   '[ESC]',  'EXIT')]
    col_kw=int(pw*0.60)   # right column key x offset from px
    for lk,ld,rk,rd in pairs:
        T(surf,lk,F(12,True),(0,210,210),(px+14,y))
        T(surf,ld,F(11),(200,140,210),(px+65,y+1))
        T(surf,rk,F(12,True),(0,210,210),(px+14+col_kw,y))
        T(surf,rd,F(11),(200,140,210),(px+14+col_kw+60,y+1))
        y+=20

# ─────────────────────────────────────────────
#  Bottom bar
# ─────────────────────────────────────────────
def draw_bottom(surf,cur_algo,path_found):
    r=pygame.Rect(0,HEIGHT-BOTTOM_H,WIDTH,BOTTOM_H)
    rr(surf,(18,5,30),r)
    pygame.draw.line(surf,(0,200,200),(0,HEIGHT-BOTTOM_H),(WIDTH,HEIGHT-BOTTOM_H),2)
    ac=ACOL[cur_algo]
    if path_found:
        msg=f'PATH FOUND!  {cur_algo} complete -- press [N] for next algorithm or [R] for new maze.'
    else:
        msg=f'{cur_algo} ALGORITHM CURRENTLY DEMONSTRATING OPTIMAL EFFICIENCY AND PATHFINDING.'
    T(surf,'* '+msg,F(13,True),(0,220,220),(20,HEIGHT-BOTTOM_H+15))
    T(surf,'* PERFORMANCE METRICS',  F(11,True),ac,             (WIDTH-210,HEIGHT-BOTTOM_H+7))
    T(surf,'* COMPARATIVE ANALYSIS', F(11,True),(200,70,220),   (WIDTH-210,HEIGHT-BOTTOM_H+22))

# ─────────────────────────────────────────────
#  Animation loop
# ─────────────────────────────────────────────
def animate(screen,clock,maze,start,goal,
            cur_algo,all_orders,all_paths,cur_idx,completed, speed):

    order=all_orders[cur_idx]; path=all_paths[cur_idx]
    total=len(order)+len(path)
    step=0; auto=True; frame=0; t0=time.time()
    ox=PAD; oy=TOP_H+PAD

    while True:
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: return 'quit', speed
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE:  return 'quit', speed
                if ev.key==pygame.K_n:       return 'next', speed
                if ev.key==pygame.K_r:       return 'restart', speed
                if ev.key==pygame.K_SPACE:   auto=not auto
                if ev.key in (pygame.K_EQUALS,pygame.K_PLUS,pygame.K_UP):
                    speed=min(speed+0.5,10.0)
                if ev.key in (pygame.K_MINUS,pygame.K_DOWN):
                    speed=max(speed-0.5,0.5)


        explored_now=order[:min(step,len(order))]
        path_now=path[:max(0,step-len(order))]

        draw_bg(screen)
        draw_header(screen,frame,cur_algo)
        draw_maze(screen,maze,start,goal,explored_now,path_now,frame,ox,oy)
        draw_sidebar(screen,cur_algo,explored_now,path_now,
                     all_orders,all_paths,time.time()-t0,frame,
                     completed,speed,cur_idx)
        draw_bottom(screen,cur_algo,step>=total and len(path)>0)
        pygame.display.flip()
        clock.tick(FPS)
        frame+=1

        if auto and step<total:
            step += speed
            step = min(int(step), total)

# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
def make_icon():
    """32x32 maze icon drawn with pygame primitives — no image file needed."""
    s=pygame.Surface((32,32),pygame.SRCALPHA)
    s.fill((20,6,36))
    pygame.draw.rect(s,(0,200,200),(1,1,30,30),2,border_radius=5)
    pts=[(6,6),(6,20),(20,20),(20,12),(12,12),(12,6)]
    pygame.draw.lines(s,(0,230,255),False,pts,3)
    pygame.draw.circle(s,(255,220,50),(24,24),4)
    pygame.draw.circle(s,(255,255,255),(24,24),2)
    pygame.draw.circle(s,(255,150,200),(6,6),3)
    return s

def main():
    pygame.init()
    screen=pygame.display.set_mode((WIDTH,HEIGHT))
    pygame.display.set_caption('Maze Solver')
    pygame.display.set_icon(make_icon())
    clock=pygame.time.Clock()
    build_bg()

    def new_maze():
        m=generate_maze(GRID_ROWS,GRID_COLS)
        s=(1,1); g=(GRID_ROWS-2,GRID_COLS-2)
        m[s[0]][s[1]]=0; m[g[0]][g[1]]=0
        return m,s,g

    maze,start,goal=new_maze()

    while True:
        all_orders=[None]*4; all_paths=[None]*4
        for i,aname in enumerate(ALGO_ORDER):
            p,o=SOLVERS[aname](maze,start,goal)
            all_orders[i]=o; all_paths[i]=p

        completed=set(); restart=False

        for idx,aname in enumerate(ALGO_ORDER):
            action, speed = animate(
                screen, clock, maze, start, goal,
                aname, all_orders, all_paths, idx, completed, speed=1.0
            )
            completed.add(aname)
            if action=='quit': pygame.quit(); return
            if action=='restart':
                maze,start,goal=new_maze(); restart=True; break

        if not restart:
            maze,start,goal=new_maze()

if __name__=='__main__':
    main()