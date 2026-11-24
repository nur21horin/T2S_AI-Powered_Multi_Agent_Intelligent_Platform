type FeatureSceneProps = { scene: string; className?: string };

const props: Record<string, React.ReactNode> = {
  discover: <><rect x="207" y="117" width="102" height="59" rx="8" fill="#effff8"/><rect x="216" y="125" width="84" height="41" rx="4" fill="#a9e8d5"/><path d="m221 158 24-21 17 16 15-19 19 24Z" fill="#0c9974"/><path d="M230 177h57" stroke="#effff8" strokeWidth="5" strokeLinecap="round"/></>,
  overview: <><rect x="210" y="101" width="126" height="76" rx="9" fill="#f2fffa"/><rect x="220" y="111" width="106" height="50" rx="4" fill="#c8f4e4"/><path d="m228 151 23-24 15 12 17-19 34 31Z" fill="#13b982"/><rect x="263" y="165" width="20" height="6" rx="3" fill="#619e8b"/></>,
  profile: <><rect x="211" y="102" width="105" height="73" rx="9" fill="#f2fffa"/><circle cx="238" cy="128" r="13" fill="#f2bd91"/><path d="M220 160q18-27 37 0" fill="#08a981"/><path d="M260 121h42M260 133h34M220 168h82" stroke="#70bba0" strokeWidth="5" strokeLinecap="round"/></>,
  rooms: <><path d="M196 166v-37l44-31 45 31v37Z" fill="#effff8"/><path d="M188 132 240 94l53 38" fill="none" stroke="#087d68" strokeWidth="8" strokeLinejoin="round"/><rect x="230" y="139" width="20" height="27" rx="3" fill="#22c994"/><circle cx="277" cy="111" r="13" fill="#f3d77b"/></>,
  tasks: <><rect x="208" y="98" width="98" height="78" rx="8" fill="#f4fff9"/><path d="M221 120h10l4 5 8-10M249 120h42M221 141h10l4 5 8-10M249 141h42M221 161h10l4 5 8-10M249 161h31" fill="none" stroke="#13aa7c" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round"/></>,
  progress: <><path d="M205 171h112" stroke="#effff8" strokeWidth="6" strokeLinecap="round"/><rect x="216" y="143" width="17" height="28" rx="4" fill="#6de0bc"/><rect x="245" y="124" width="17" height="47" rx="4" fill="#31d3a0"/><rect x="274" y="105" width="17" height="66" rx="4" fill="#08a981"/><path d="m214 132 33-22 26 5 38-33" fill="none" stroke="#f3d77b" strokeWidth="4" strokeLinecap="round"/></>,
  knowledge: <><path d="M204 111q25-12 48 2v59q-23-13-48-2ZM252 113q25-14 49-2v59q-24-11-49 2Z" fill="#effff8"/><path d="M214 126h27M214 137h27M262 126h28M262 137h28" stroke="#19b787" strokeWidth="4" strokeLinecap="round"/><path d="m300 98 10 10-24 25-10 2 2-10Z" fill="#f3d77b"/></>,
  research: <><path d="M238 98v34l-28 42q-5 9 7 9h48q12 0 7-10l-28-41V98" fill="#effff8"/><path d="M222 158h46l11 18q4 7-5 7h-49q-10 0-5-8Z" fill="#28d19b"/><path d="M229 98h30M232 146h21" stroke="#087d68" strokeWidth="6" strokeLinecap="round"/><circle cx="245" cy="168" r="4" fill="#f3d77b"/></>,
  career: <><rect x="203" y="119" width="108" height="62" rx="10" fill="#effff8"/><path d="M232 119v-11q0-8 9-8h31q9 0 9 8v11" fill="none" stroke="#effff8" strokeWidth="7"/><path d="M203 140h108M250 137v11h14v-11" fill="none" stroke="#18bb89" strokeWidth="6"/><path d="m281 102 12 12 24-27" fill="none" stroke="#f3d77b" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/></>,
  student: <><rect x="202" y="131" width="102" height="58" rx="7" fill="#effff8"/><rect x="210" y="138" width="86" height="42" rx="3" fill="#a9e8d5"/><path d="m216 171 20-18 15 12 14-16 25 22Z" fill="#0c9974"/><path d="M233 190h41" stroke="#effff8" strokeWidth="6" strokeLinecap="round"/><circle cx="310" cy="113" r="18" fill="#f3d77b"/><path d="M298 110h24" stroke="#087d68" strokeWidth="4" strokeLinecap="round"/></>,
  teacher: <><rect x="197" y="104" width="110" height="73" rx="7" fill="#effff8"/><path d="M212 124h78M212 140h54M212 157h68" stroke="#18b787" strokeWidth="5" strokeLinecap="round"/><path d="m213 165 15-16 11 8 15-17" fill="none" stroke="#f3d77b" strokeWidth="4"/><circle cx="299" cy="99" r="9" fill="#f3d77b"/></>,
  alumni: <><path d="m197 118 55-24 57 24-57 24Z" fill="#effff8"/><path d="M218 129v26q34 24 69 0v-26" fill="#c3efdf"/><path d="M306 121v33" stroke="#f3d77b" strokeWidth="5"/><circle cx="306" cy="158" r="6" fill="#f3d77b"/><path d="M240 112h25" stroke="#14a87e" strokeWidth="5" strokeLinecap="round"/></>,
};

export default function FeatureScene({ scene, className = "" }: FeatureSceneProps) {
  return (
    <div className={`feature-scene ${className}`} aria-hidden="true">
      <svg viewBox="0 0 420 220" role="presentation">
        <defs><linearGradient id="scene-sky" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#10162b"/><stop offset="1" stopColor="#08708a"/></linearGradient><linearGradient id="scene-aurora" x1="0" y1="0" x2="1" y2="0"><stop stopColor="#58ffbb" stopOpacity="0"/><stop offset=".55" stopColor="#0ce6a1" stopOpacity=".8"/><stop offset="1" stopColor="#38d9cf" stopOpacity="0"/></linearGradient></defs>
        <rect width="420" height="220" rx="20" fill="url(#scene-sky)"/>
        <g className="scene-stars" fill="#e6f9e9"><circle cx="42" cy="28" r="1.5"/><circle cx="109" cy="54" r="1.2"/><circle cx="180" cy="25" r="1.8"/><circle cx="273" cy="47" r="1.3"/><circle cx="321" cy="20" r="1.6"/></g>
        <path className="scene-aurora" d="M-20 72q88-40 163 0t155 1q51-13 113-8" fill="none" stroke="url(#scene-aurora)" strokeWidth="18" strokeLinecap="round"/>
        <circle className="scene-sun" cx="355" cy="42" r="21" fill="#f3d77b"/>
        <path d="m0 141 78-61 58 43 70-76 84 92 61-54 69 54v81H0Z" fill="#15566a"/>
        <path d="m160 105 46-58 55 77-29-17-25 14-22-16-18 14Z" fill="#8eeed0"/>
        <path d="m0 177 86-62 68 47 67-47 78 61 56-43 65 43v44H0Z" fill="#073b55"/>
        <path d="M0 194q90-30 180 0t180 0 60 0v26H0Z" fill="#041d32"/>
        {props[scene] ?? props.overview}
        <g className="scene-person scene-person-one">
          <path d="M340 150q-12 19-10 38l-5 24h12l10-22 7 22h12l-4-31q4-16-5-31Z" fill="#064c45"/>
          <path d="M337 148q-8-17 4-25 15-8 23 5 4 9-2 20l-6 8h-14Z" fill="#f2bd91"/>
          <path d="M333 138q-2-19 16-23 15 1 17 14l-9-4-10 5-7 13Z" fill="#083d39"/>
          <path d="M341 154q-11 11-19 17l-16-8-5 8 20 12q5 2 10-3l17-13" fill="#0bbd8a" stroke="#0bbd8a" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M358 155q14 3 17 17l9 2-2 8-15-3q-5-1-7-7l-9-8" fill="#0bbd8a" stroke="#0bbd8a" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round"/>
          <circle className="scene-eye" cx="354" cy="143" r="1.7" fill="#073b36"/>
        </g>
        <g className="scene-person scene-person-two">
          <path d="M119 161q-8 13-6 28l-5 22h11l9-19 5 19h11l-3-28q4-13-4-22Z" fill="#0a5d52"/>
          <path d="M116 157q-7-14 3-22 12-6 19 5 3 8-2 17l-5 6h-11Z" fill="#d99e75"/>
          <path d="M112 148q-2-16 13-19 13 0 16 12l-9-3-8 4-6 11Z" fill="#293f52"/>
          <path d="M121 163q-8 7-10 17l-12 7-5-6 13-12 6-11" fill="#f3d77b" stroke="#f3d77b" strokeWidth="8" strokeLinecap="round" strokeLinejoin="round"/>
          <path d="M137 162q9 8 13 18l12 2v7l-17-1q-5 0-7-5l-8-10" fill="#f3d77b" stroke="#f3d77b" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round"/>
          <circle className="scene-eye" cx="130" cy="155" r="1.5" fill="#073b36"/>
        </g>
        <path d="M65 197h15l-8-24Z" fill="#28d19b"/><path d="M75 197h15l-13-24Z" fill="#087d68"/>
        <path className="scene-sparkle" d="m390 102 3 8 8 3-8 3-3 8-3-8-8-3 8-3Z" fill="#fff2ad"/>
        <path className="scene-sparkle scene-sparkle-two" d="m95 91 2 5 5 2-5 2-2 5-2-5-5-2 5-2Z" fill="#effff8"/>
      </svg>
    </div>
  );
}
