import { createContext, useContext, useMemo, useRef, useState, type ReactNode } from "react";

export type FarmerProfile = { name: string; phone: string; province: string; municipality: string; farmName: string; farmSizeHa: number; cornVariety: string };
export type FarmRecord = { id: string; cropName: string; plantingDate: string; harvestDate: string; quantityKg: number; seedCost: number; fertilizerCost: number; pesticideCost: number; laborCost: number; otherCost: number; salesIncome: number; notes: string; createdAt: string; isDemo: boolean };
export type ProductPrice = { id: string; productName: string; category: string; price: number; unit: string; storeOrMarket: string; location: string; source: string; updatedAt: string; isDemo: boolean };
export type BuyerLead = { id: string; buyerName: string; contactName: string; phone: string; email: string; location: string; offeredPricePerKg: number; quantityKg: number; status: string; notes: string; createdAt: string };
export type CommunityPost = { id: string; title: string; body: string; author: string; location: string; kind: string; createdAt: string; isDemo: boolean };
export type PlannerDraft = { area: string; yieldKg: string; price: string; costs: { seed: string; fertilizer: string; pesticide: string; labor: string; other: string } };
type AppData = { profile: FarmerProfile; records: FarmRecord[]; prices: ProductPrice[]; buyers: BuyerLead[]; posts: CommunityPost[]; plannerDraft: PlannerDraft };
type Store = AppData & { storageError: string | null; updateProfile: (p: FarmerProfile) => boolean; updatePlannerDraft: (draft: PlannerDraft) => boolean; saveRecord: (r: FarmRecord) => boolean; deleteRecord: (id: string) => boolean; savePrice: (p: ProductPrice) => boolean; deletePrice: (id: string) => boolean; saveBuyer: (b: BuyerLead) => boolean; deleteBuyer: (id: string) => boolean; addPost: (p: CommunityPost) => boolean; deletePost: (id:string) => boolean };
const KEY = "cornprofit-connect-v1";

const initialData: AppData = {
  profile: { name: "Maria Santos", phone: "0917 284 6130", province: "Isabela", municipality: "Ilagan", farmName: "Santos Family Farm", farmSizeHa: 2.4, cornVariety: "Dekalb DK 9901" },
  records: [
    { id:"demo-r1", cropName:"Yellow corn · Season 2025", plantingDate:"2025-01-12", harvestDate:"2025-05-08", quantityKg:7380, seedCost:8400, fertilizerCost:21800, pesticideCost:5600, laborCost:14700, otherCost:3200, salesIncome:132840, notes:"Good stand after early rains. Sold to local trader.", createdAt:"2025-05-08", isDemo:true },
    { id:"demo-r2", cropName:"Yellow corn · Season 2024", plantingDate:"2024-08-19", harvestDate:"2024-12-11", quantityKg:6240, seedCost:7800, fertilizerCost:18600, pesticideCost:4800, laborCost:12600, otherCost:2600, salesIncome:106080, notes:"Second crop; dried on family-owned slab.", createdAt:"2024-12-11", isDemo:true },
    { id:"demo-r3", cropName:"White corn · Season 2024", plantingDate:"2024-03-04", harvestDate:"2024-06-28", quantityKg:4180, seedCost:6200, fertilizerCost:15100, pesticideCost:3900, laborCost:10900, otherCost:2100, salesIncome:71060, notes:"A smaller trial plot near the creek.", createdAt:"2024-06-28", isDemo:true },
  ],
  prices: [
    {id:"demo-p1",productName:"Yellow corn, dried",category:"Farmgate buyer quote",price:18,unit:"kg",storeOrMarket:"Example local trader",location:"Ilagan, Isabela",source:"Fictional sample, not verified",updatedAt:"2025-05-22",isDemo:true},
    {id:"demo-p2",productName:"Yellow corn, wet",category:"Farmgate buyer quote",price:13.5,unit:"kg",storeOrMarket:"Example buying station",location:"Cauayan, Isabela",source:"Fictional sample, not verified",updatedAt:"2025-05-20",isDemo:true},
    {id:"demo-p3",productName:"Hybrid corn seed",category:"Farm input",price:2850,unit:"20 kg bag",storeOrMarket:"Example agri supply",location:"Santiago City, Isabela",source:"Fictional sample, not verified",updatedAt:"2025-05-18",isDemo:true},
    {id:"demo-p4",productName:"Complete fertilizer 14-14-14",category:"Farm input",price:1560,unit:"50 kg bag",storeOrMarket:"Example agri supply",location:"Ilagan, Isabela",source:"Fictional sample, not verified",updatedAt:"2025-05-17",isDemo:true},
    {id:"demo-p5",productName:"Urea 46-0-0",category:"Farm input",price:1480,unit:"50 kg bag",storeOrMarket:"Example agri supply",location:"Tumauini, Isabela",source:"Fictional sample, not verified",updatedAt:"2025-05-16",isDemo:true},
  ],
  buyers: [
    {id:"demo-b1",buyerName:"Cagayan Valley Grain Hub",contactName:"Ramon Dela Cruz",phone:"0918 672 4031",email:"",location:"Ilagan, Isabela",offeredPricePerKg:18.2,quantityKg:10000,status:"Interested",notes:"Example lead only. Confirm weighing, moisture and payment terms.",createdAt:"2025-05-20"},
    {id:"demo-b2",buyerName:"Northern Harvest Trading",contactName:"Liza Ramos",phone:"0920 334 1862",email:"",location:"Cauayan, Isabela",offeredPricePerKg:17.75,quantityKg:7000,status:"Contacted",notes:"Example lead only. Ask if hauling is included.",createdAt:"2025-05-18"},
  ],
  posts: [
    {id:"demo-c1",title:"Check grain moisture before agreeing on a price",body:"A simple moisture check can prevent surprises at weighing. Ask the buyer what moisture level their price assumes, and write down any drying deductions before you load.",author:"CornProfit field note",location:"Isabela",kind:"Tip",createdAt:"2025-05-21",isDemo:true},
    {id:"demo-c2",title:"Group selling meet-up · sample announcement",body:"Farmers in the barangay can compare available volume before calling buyers. This is a sample community notice, not a real event.",author:"Community board example",location:"Ilagan, Isabela",kind:"Announcement",createdAt:"2025-05-17",isDemo:true},
    {id:"demo-c3",title:"Keep a small notebook for every input purchase",body:"Date, product, quantity and cost are enough to make your end-of-season estimate more useful. Take a photo of the receipt if you have a phone.",author:"CornProfit field note",location:"Cagayan Valley",kind:"Tip",createdAt:"2025-05-12",isDemo:true},
  ],
  plannerDraft: { area:"2.4", yieldKg:"6500", price:"18", costs:{seed:"8500",fertilizer:"21000",pesticide:"5500",labor:"14000",other:"3000"} },
};

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function number(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function loadData(): { data: AppData; storageError: string | null } {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved) {
      const parsed: unknown = JSON.parse(saved);
      if (!isObject(parsed)) throw new Error("Saved data is not an object.");
      const readList = <T,>(key: string, fallback: T[], normalize: (value: unknown) => T): T[] => {
        if (parsed[key] === undefined) return fallback;
        if (!Array.isArray(parsed[key])) throw new Error(`Saved ${key} are not a list.`);
        return (parsed[key] as unknown[]).map(normalize);
      };
      const profile = parsed.profile === undefined ? initialData.profile : parsed.profile;
      if (!isObject(profile)) throw new Error("Saved farm profile is not valid.");
      return {
        data: {
          profile: {
            name: text(profile.name, initialData.profile.name),
            phone: text(profile.phone, initialData.profile.phone),
            province: text(profile.province, initialData.profile.province),
            municipality: text(profile.municipality, initialData.profile.municipality),
            farmName: text(profile.farmName, initialData.profile.farmName),
            farmSizeHa: number(profile.farmSizeHa, initialData.profile.farmSizeHa),
            cornVariety: text(profile.cornVariety, initialData.profile.cornVariety),
          },
          records: readList("records", initialData.records, value => {
            const r = isObject(value) ? value : {};
            return {
              id: text(r.id, makeId()), cropName: text(r.cropName, "Untitled crop"),
              plantingDate: text(r.plantingDate), harvestDate: text(r.harvestDate),
              quantityKg: number(r.quantityKg), seedCost: number(r.seedCost),
              fertilizerCost: number(r.fertilizerCost), pesticideCost: number(r.pesticideCost),
              laborCost: number(r.laborCost), otherCost: number(r.otherCost),
              salesIncome: number(r.salesIncome), notes: text(r.notes),
              createdAt: text(r.createdAt), isDemo: r.isDemo === true,
            };
          }),
          prices: readList("prices", initialData.prices, value => {
            const p = isObject(value) ? value : {};
            return {
              id: text(p.id, makeId()), productName: text(p.productName, "Unnamed product"),
              category: text(p.category, "Other"), price: number(p.price), unit: text(p.unit, "unit"),
              storeOrMarket: text(p.storeOrMarket, text(p.source, "Not specified")),
              location: text(p.location, "Not specified"), source: text(p.source, "Manual entry"),
              updatedAt: text(p.updatedAt), isDemo: p.isDemo === true,
            };
          }),
          buyers: readList("buyers", initialData.buyers, value => {
            const b = isObject(value) ? value : {};
            return {
              id: text(b.id, makeId()), buyerName: text(b.buyerName, "Unnamed buyer"),
              contactName: text(b.contactName), phone: text(b.phone), email: text(b.email),
              location: text(b.location), offeredPricePerKg: number(b.offeredPricePerKg),
              quantityKg: number(b.quantityKg), status: text(b.status, "New"),
              notes: text(b.notes), createdAt: text(b.createdAt),
            };
          }),
          posts: readList("posts", initialData.posts, value => {
            const p = isObject(value) ? value : {};
            return {
              id: text(p.id, makeId()), title: text(p.title, "Untitled tip"),
              body: text(p.body), author: text(p.author), location: text(p.location),
              kind: text(p.kind, "Tip"), createdAt: text(p.createdAt), isDemo: p.isDemo === true,
            };
          }),
          plannerDraft: (() => {
            const draft = parsed.plannerDraft === undefined ? initialData.plannerDraft : parsed.plannerDraft;
            if (!isObject(draft)) throw new Error("Saved planner estimate is not valid.");
            const draftCosts = isObject(draft.costs) ? draft.costs : initialData.plannerDraft.costs;
            return {
              area: text(draft.area, initialData.plannerDraft.area),
              yieldKg: text(draft.yieldKg, initialData.plannerDraft.yieldKg),
              price: text(draft.price, initialData.plannerDraft.price),
              costs: {
                seed: text(draftCosts.seed, initialData.plannerDraft.costs.seed),
                fertilizer: text(draftCosts.fertilizer, initialData.plannerDraft.costs.fertilizer),
                pesticide: text(draftCosts.pesticide, initialData.plannerDraft.costs.pesticide),
                labor: text(draftCosts.labor, initialData.plannerDraft.costs.labor),
                other: text(draftCosts.other, initialData.plannerDraft.costs.other),
              },
            };
          })(),
        },
        storageError: null,
      };
    }
    localStorage.setItem(KEY, JSON.stringify(initialData));
  } catch {
    return {
      data: initialData,
      storageError: "Saved data could not be read or written. Changes will not be shown as saved until browser storage is available.",
    };
  }
  return { data: initialData, storageError: null };
}
const StoreContext = createContext<Store | null>(null);
export function AppStore({ children }: { children: ReactNode }) {
  const [initial] = useState(loadData);
  const [data, setData] = useState<AppData>(initial.data);
  const [storageError, setStorageError] = useState<string | null>(initial.storageError);
  const dataRef = useRef(initial.data);
  const commit = (update: (current: AppData) => AppData): boolean => {
    const next = update(dataRef.current);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
      dataRef.current = next;
      setData(next);
      setStorageError(null);
      return true;
    } catch {
      setStorageError("Could not save to this browser. Free up browser storage or check its privacy settings, then try again.");
      return false;
    }
  };
  const value = useMemo<Store>(() => ({
    ...data,
    storageError,
    updateProfile: (profile) => commit(d => ({ ...d, profile })),
    updatePlannerDraft: (plannerDraft) => commit(d => ({ ...d, plannerDraft })),
    saveRecord: (record) => commit(d => ({ ...d, records: [record, ...d.records.filter(r => r.id !== record.id)] })),
    deleteRecord: (id) => commit(d => ({ ...d, records: d.records.filter(r => r.id !== id) })),
    savePrice: (price) => commit(d => ({ ...d, prices: [price, ...d.prices.filter(p => p.id !== price.id)] })),
    deletePrice: (id) => commit(d => ({ ...d, prices: d.prices.filter(p => p.id !== id) })),
    saveBuyer: (buyer) => commit(d => ({ ...d, buyers: [buyer, ...d.buyers.filter(b => b.id !== buyer.id)] })),
    deleteBuyer: (id) => commit(d => ({ ...d, buyers: d.buyers.filter(b => b.id !== id) })),
    addPost: (post) => commit(d => ({ ...d, posts: [post, ...d.posts] })),
    deletePost: (id) => commit(d => ({ ...d, posts: d.posts.filter(p => p.id !== id) })),
  }), [data, storageError]);
  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}
export function useAppStore() {
  const value = useContext(StoreContext);
  if (!value) throw new Error("useAppStore must be used inside AppStore");
  return value;
}
export const makeId = () => `${Date.now()}-${Math.random().toString(36).slice(2,8)}`;
export const recordCost = (r: FarmRecord) => r.seedCost + r.fertilizerCost + r.pesticideCost + r.laborCost + r.otherCost;
export const peso = (amount: number) => new Intl.NumberFormat("en-PH", { style:"currency", currency:"PHP", maximumFractionDigits: amount % 1 ? 2 : 0 }).format(amount || 0);
