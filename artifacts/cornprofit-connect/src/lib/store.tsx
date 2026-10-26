import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type FarmerProfile = { name: string; phone: string; province: string; municipality: string; farmName: string; farmSizeHa: number; cornVariety: string };
export type FarmRecord = { id: string; cropName: string; plantingDate: string; harvestDate: string; quantityKg: number; seedCost: number; fertilizerCost: number; pesticideCost: number; laborCost: number; otherCost: number; salesIncome: number; notes: string; createdAt: string; isDemo: boolean };
export type ProductPrice = { id: string; productName: string; category: string; price: number; unit: string; location: string; source: string; updatedAt: string; isDemo: boolean };
export type BuyerLead = { id: string; buyerName: string; contactName: string; phone: string; email: string; location: string; offeredPricePerKg: number; quantityKg: number; status: string; notes: string; createdAt: string };
export type CommunityPost = { id: string; title: string; body: string; author: string; location: string; kind: string; createdAt: string; isDemo: boolean };
type AppData = { profile: FarmerProfile; records: FarmRecord[]; prices: ProductPrice[]; buyers: BuyerLead[]; posts: CommunityPost[] };
type Store = AppData & { updateProfile: (p: FarmerProfile) => void; saveRecord: (r: FarmRecord) => void; deleteRecord: (id: string) => void; savePrice: (p: ProductPrice) => void; deletePrice: (id: string) => void; saveBuyer: (b: BuyerLead) => void; deleteBuyer: (id: string) => void; addPost: (p: CommunityPost) => void; deletePost: (id:string) => void };
const KEY = "cornprofit-connect-v1";

const initialData: AppData = {
  profile: { name: "Maria Santos", phone: "0917 284 6130", province: "Isabela", municipality: "Ilagan", farmName: "Santos Family Farm", farmSizeHa: 2.4, cornVariety: "Dekalb DK 9901" },
  records: [
    { id:"demo-r1", cropName:"Yellow corn · Season 2025", plantingDate:"2025-01-12", harvestDate:"2025-05-08", quantityKg:7380, seedCost:8400, fertilizerCost:21800, pesticideCost:5600, laborCost:14700, otherCost:3200, salesIncome:132840, notes:"Good stand after early rains. Sold to local trader.", createdAt:"2025-05-08", isDemo:true },
    { id:"demo-r2", cropName:"Yellow corn · Season 2024", plantingDate:"2024-08-19", harvestDate:"2024-12-11", quantityKg:6240, seedCost:7800, fertilizerCost:18600, pesticideCost:4800, laborCost:12600, otherCost:2600, salesIncome:106080, notes:"Second crop; dried on family-owned slab.", createdAt:"2024-12-11", isDemo:true },
    { id:"demo-r3", cropName:"White corn · Season 2024", plantingDate:"2024-03-04", harvestDate:"2024-06-28", quantityKg:4180, seedCost:6200, fertilizerCost:15100, pesticideCost:3900, laborCost:10900, otherCost:2100, salesIncome:71060, notes:"A smaller trial plot near the creek.", createdAt:"2024-06-28", isDemo:true },
  ],
  prices: [
    {id:"demo-p1",productName:"Yellow corn, dried",category:"Farmgate buyer quote",price:18,unit:"kg",location:"Ilagan, Isabela",source:"Example local trader",updatedAt:"2025-05-22",isDemo:true},
    {id:"demo-p2",productName:"Yellow corn, wet",category:"Farmgate buyer quote",price:13.5,unit:"kg",location:"Cauayan, Isabela",source:"Example buying station",updatedAt:"2025-05-20",isDemo:true},
    {id:"demo-p3",productName:"Hybrid corn seed",category:"Farm input",price:2850,unit:"20 kg bag",location:"Santiago City, Isabela",source:"Example agri supply",updatedAt:"2025-05-18",isDemo:true},
    {id:"demo-p4",productName:"Complete fertilizer 14-14-14",category:"Farm input",price:1560,unit:"50 kg bag",location:"Ilagan, Isabela",source:"Example agri supply",updatedAt:"2025-05-17",isDemo:true},
    {id:"demo-p5",productName:"Urea 46-0-0",category:"Farm input",price:1480,unit:"50 kg bag",location:"Tumauini, Isabela",source:"Example agri supply",updatedAt:"2025-05-16",isDemo:true},
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
};

function loadData(): AppData {
  try {
    const saved = localStorage.getItem(KEY);
    if (saved) return { ...initialData, ...JSON.parse(saved) as Partial<AppData> };
    localStorage.setItem(KEY, JSON.stringify(initialData));
  } catch { /* local storage may be unavailable; the session remains usable */ }
  return initialData;
}
const StoreContext = createContext<Store | null>(null);
export function AppStore({ children }: { children: ReactNode }) {
  const [data, setData] = useState<AppData>(loadData);
  useEffect(() => { try { localStorage.setItem(KEY, JSON.stringify(data)); } catch { /* keep in-memory state */ } }, [data]);
  const value = useMemo<Store>(() => ({
    ...data,
    updateProfile: (profile) => setData(d => ({ ...d, profile })),
    saveRecord: (record) => setData(d => ({ ...d, records: [record, ...d.records.filter(r => r.id !== record.id)] })),
    deleteRecord: (id) => setData(d => ({ ...d, records: d.records.filter(r => r.id !== id) })),
    savePrice: (price) => setData(d => ({ ...d, prices: [price, ...d.prices.filter(p => p.id !== price.id)] })),
    deletePrice: (id) => setData(d => ({ ...d, prices: d.prices.filter(p => p.id !== id) })),
    saveBuyer: (buyer) => setData(d => ({ ...d, buyers: [buyer, ...d.buyers.filter(b => b.id !== buyer.id)] })),
    deleteBuyer: (id) => setData(d => ({ ...d, buyers: d.buyers.filter(b => b.id !== id) })),
    addPost: (post) => setData(d => ({ ...d, posts: [post, ...d.posts] })),
    deletePost: (id) => setData(d => ({ ...d, posts: d.posts.filter(p => p.id !== id) })),
  }), [data]);
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
