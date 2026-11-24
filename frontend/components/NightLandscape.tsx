const stars = [
  [4, 14, 2], [7, 7, 1.3], [12, 19, 2.6], [17, 10, 1.5], [22, 17, 2.2],
  [28, 8, 1.4], [34, 20, 2.8], [39, 12, 1.5], [45, 6, 2.3], [51, 18, 1.6],
  [57, 9, 2.7], [63, 21, 1.4], [69, 7, 1.9], [75, 15, 2.5], [81, 9, 1.5],
  [87, 19, 2.2], [93, 7, 1.4], [97, 16, 2.4], [11, 30, 1.5], [25, 27, 2.1],
  [43, 28, 1.3], [58, 31, 2.2], [72, 28, 1.4], [90, 31, 2],
];

const trees = Array.from({ length: 82 }, (_, i) => {
  const x = i * 21 - 10;
  const y = 674 + ((i * 37) % 150);
  const h = 60 + ((i * 29) % 100);
  const w = h * 0.39;
  const shade = i % 3 === 0 ? "#031b2b" : i % 3 === 1 ? "#05243a" : "#06304a";
  return <path key={i} d={`M${x} ${y}l${w * .5} -${h} ${w * .5} ${h * .37} -${w * .23} -${h * .1} ${w * .23} ${h * .34} -${w * .27} -${h * .08} ${w * .27} ${h * .36} -${w * .3} -${h * .08} ${w * .3} ${h * .19}Z`} fill={shade} opacity={.55 + (i % 4) * .1} />;
});

export default function NightLandscape() {
  return (
    <div className="night-landscape" aria-hidden="true">
      <svg viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" role="presentation">
        <defs>
          <linearGradient id="night-sky" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#10162b"/><stop offset=".52" stopColor="#123b52"/><stop offset="1" stopColor="#07506a"/></linearGradient>
          <linearGradient id="aurora" x1="0" y1="0" x2="1" y2=".4"><stop stopColor="#38f5a2"/><stop offset=".5" stopColor="#00c996"/><stop offset="1" stopColor="#087b9a"/></linearGradient>
          <linearGradient id="horizon" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#06425b"/><stop offset="1" stopColor="#031c2d"/></linearGradient>
        </defs>
        <rect width="1600" height="900" fill="url(#night-sky)"/>
        <g className="night-stars">{stars.map(([x,y,r], i) => <circle key={i} cx={`${x}%`} cy={`${y}%`} r={r} fill="#e4f4df" opacity={i % 3 === 0 ? .85 : .52} />)}</g>
        <path className="aurora-ribbon" d="M720-40C575 90 575 210 706 286c104 60 304 36 307 145 2 91-183 96-211 179 72-59 214-40 266-122 68-106-46-185-179-207C707 246 710 165 817 35Z" fill="url(#aurora)" opacity=".95"/>
        <path d="M350 583 648 430l122 82 144-190 134 164 111-95 163 143 108-77 170 117v326H350Z" fill="#063149"/>
        <path d="m846 428 68-106 70 109-37-26-34 22-30-20-23 21Z" fill="#071c2b"/>
        <path d="m1230 483 88-92 100 101-48-29-45 29-40-26-28 24Z" fill="#061827"/>
        <path d="M0 635q174-108 360-4 151-88 300-10 201-90 385-1 225-103 555 12v268H0Z" fill="url(#horizon)"/>
        <g className="forest-trees">{trees}</g>
        <g className="front-forest">{Array.from({length: 28}, (_,i) => { const x=i*62-15; const h=135+(i*43%115); const w=h*.47; return <path key={i} d={`M${x} 920l${w/2} -${h} ${w/2} ${h*.4} -${w*.23} -${h*.13} ${w*.23} ${h*.39} -${w*.3} -${h*.12} ${w*.3} ${h*.46}Z`} fill="#021521"/>; })}</g>
        <path className="left-curve-panel" d="M0 0h790C687 91 631 167 641 258c12 111 87 169-8 249-103 88-218 123-263 240-20 51-20 105-31 153H0Z" fill="#052b3d"/>
      </svg>
    </div>
  );
}
