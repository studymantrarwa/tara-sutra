export type BirthData={name:string;gender:string;dob:string;time:string;placeId:string;placeLabel:string;latitude:number;longitude:number;timezone:string};
export async function calculateKundli(data:BirthData){
  const base=process.env.NEXT_PUBLIC_ASTRO_ENGINE_URL || process.env.ASTRO_ENGINE_URL || "http://127.0.0.1:8000";
  const r=await fetch(base+"/calculate",{method:"POST",headers:{"content-type":"application/json"},body:JSON.stringify(data)});
  if(!r.ok) throw new Error("Astrology engine calculation failed");
  return r.json();
}