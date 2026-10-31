import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from decimal import Decimal
from database import init_db, db, now_text
from auth import register, login
from calculations import (money, sum_amounts, profit_loss, budget_total, budget_shortage,
    capital_remaining, break_even_price, estimated_revenue, fuel_cost, transport_total,
    buyer_gross, buyer_net, group_quantity, allocate_shared_cost)

st.set_page_config(page_title="CornProfit Connect", page_icon="🌽", layout="wide")
init_db()

EXPENSE_CATEGORIES = ["Seeds","Fertilizer","Pesticides and crop protection","Land preparation","Labor","Fuel","Irrigation","Equipment rental","Planting expenses","Harvesting expenses","Drying and processing","Transportation","Packaging and storage","Other expenses"]
BUDGET_CATEGORIES = ["Seeds","Fertilizer","Pesticides and crop protection","Land preparation","Labor","Fuel","Irrigation","Equipment rental","Planting","Harvesting","Drying and processing","Transportation","Storage and packaging","Other expenses"]
PRICE_CATEGORIES = ["Corn seeds","Fertilizer","Pesticides and crop protection","Fuel","Other farm supplies"]
UNITS = ["kg","g","L","mL","bag","sack","piece","hour","day","trip","hectare","other"]

def query(sql, args=()):
    with db() as con:
        return pd.read_sql_query(sql, con, params=args)

def execute(sql, args=()):
    with db() as con:
        cur = con.execute(sql, args)
        return cur.lastrowid

def farm_options(uid):
    df = query("SELECT id,name FROM farm_records WHERE user_id=? ORDER BY id DESC", (uid,))
    return df

def fmt(x):
    try: return f"₱{float(x):,.2f}"
    except (ValueError, TypeError): return "₱0.00"

def show_df(df, empty="No records yet. Add one using the form above."):
    if df.empty: st.info(empty)
    else: st.dataframe(df, use_container_width=True, hide_index=True)

def add_demo(uid):
    # Clearly labelled demo data; only added for the current user.
    with db() as con:
        existing = con.execute("SELECT id FROM farm_records WHERE user_id=? AND name='DEMO — Corn production cycle'", (uid,)).fetchone()
        if not existing:
            cur = con.execute("""INSERT INTO farm_records(user_id,name,crop_type,planting_date,harvest_date,location,area_ha,expected_kg,actual_kg,notes,status,created_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""", (uid,"DEMO — Corn production cycle","Corn",str(date.today()),"", "Sample municipality",1,3000,0,"DEMONSTRATION ONLY","ongoing",now_text()))
            fid = cur.lastrowid
            con.execute("INSERT INTO expenses(user_id,farm_id,date,category,description,quantity,unit,unit_price,amount,supplier,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (uid,fid,str(date.today()),"Seeds","DEMO seed expense",2,"bag",1200,2400,"Sample supplier","SAMPLE DATA"))
            con.execute("INSERT INTO income(user_id,farm_id,date,quantity_kg,price_per_kg,gross_sales,other_income,buyer,notes) VALUES(?,?,?,?,?,?,?,?,?)",
                        (uid,fid,str(date.today()),1000,14,14000,0,"Sample buyer","SAMPLE DATA"))
        con.execute("INSERT INTO price_reports(user_id,product,category,brand,package_size,unit,price,supplier,location,reported_at,verified_at,verification,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (uid,"DEMO urea fertilizer","Fertilizer","Sample brand",50,"kg",1800,"Demo supply store","Sample municipality",now_text(),None,"Unverified","SAMPLE DATA — NOT VERIFIED"))
        con.execute("INSERT INTO buyer_offers(user_id,buyer,location,price_per_kg,min_kg,max_kg,corn_type,moisture,fixed_deduction,percent_deduction,payment_terms,delivery,expires,updated_at,verification,contact,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (uid,"DEMO corn buyer","Sample municipality",14,500,5000,"Yellow corn","Confirm with buyer",0,0,"Confirm before sale","Pickup terms to confirm","",now_text(),"Unverified","demo@example.invalid","SAMPLE OFFER — NOT VERIFIED"))

def auth_screen():
    st.title("🌽 CornProfit Connect")
    st.subheader("Farm finances, clearer decisions.")
    st.write("Track corn production costs, plan a budget, compare supply prices and buyer offers, and estimate group-selling costs.")
    tab1, tab2 = st.tabs(["Log in", "Create account"])
    with tab1:
        with st.form("login_form"):
            contact = st.text_input("Email or phone")
            password = st.text_input("Password", type="password")
            go = st.form_submit_button("Log in", type="primary")
        if go:
            uid = login(contact, password)
            if uid:
                st.session_state.user_id = uid
                st.rerun()
            else: st.error("Login failed. Check your contact and password.")
    with tab2:
        with st.form("register_form"):
            full = st.text_input("Full name")
            contact = st.text_input("Email or phone", key="reg_contact")
            password = st.text_input("Password (at least 8 characters)", type="password", key="reg_pw")
            municipality = st.text_input("Municipality")
            barangay = st.text_input("Barangay")
            farm = st.text_input("Farm name (optional)")
            go = st.form_submit_button("Create account", type="primary")
        if go:
            if not full.strip() or not contact.strip() or len(password) < 8:
                st.error("Enter your name, contact, and a password of at least 8 characters.")
            else:
                try:
                    st.session_state.user_id = register(full, contact, password, municipality, barangay, farm)
                    st.success("Account created. Welcome!")
                    st.rerun()
                except Exception as e: st.error(f"Could not create account. Contact may already be registered. Details: {e}")
    st.caption("Local prototype: account data stays in this computer's SQLite database. Not a production authentication service.")

if "user_id" not in st.session_state:
    auth_screen()
    st.stop()

uid = st.session_state.user_id
user = query("SELECT * FROM users WHERE id=?", (uid,))
if user.empty:
    st.session_state.clear(); st.rerun()
user = user.iloc[0]
st.sidebar.markdown("# 🌽 CornProfit")
st.sidebar.caption("Connect farm costs to better decisions")
pages = ["Dashboard","Farm Expenses and Profit Tracker","CornCost Planner","CornPrice Watch","CornBulk Connect","Farm Records","Community","Profile","Settings"]
page = st.sidebar.radio("Navigate", pages)
st.sidebar.divider()
st.sidebar.caption(f"Signed in as **{user['full_name']}**")
if st.sidebar.button("Log out"):
    st.session_state.clear(); st.rerun()

farms = farm_options(uid)
farm_labels = {int(r.id): r.name for r in farms.itertuples()} if not farms.empty else {}
farm_ids = list(farm_labels)
farm_select_labels = ["All / unassigned"] + [f"{i} — {n}" for i,n in farm_labels.items()]
def selected_farm(label):
    try: return int(label.split(" — ",1)[0])
    except Exception: return None

if page == "Dashboard":
    st.title("Dashboard")
    st.caption("Your farm finances at a glance. Figures are based only on records you have entered.")
    ex = query("SELECT COALESCE(SUM(amount),0) total FROM expenses WHERE user_id=?", (uid,)).iloc[0]["total"]
    inc = query("SELECT COALESCE(SUM(gross_sales+other_income),0) total FROM income WHERE user_id=?", (uid,)).iloc[0]["total"]
    budget = query("SELECT COALESCE(SUM(capital),0) capital, COALESCE(SUM((SELECT COALESCE(SUM(total),0) FROM budget_items bi WHERE bi.budget_id=budgets.id)),0) planned FROM budgets WHERE user_id=?", (uid,)).iloc[0]
    pl = float(inc)-float(ex)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Recorded expenses",fmt(ex)); c2.metric("Recorded income",fmt(inc)); c3.metric("Recorded profit / loss",fmt(pl),delta=None)
    c4.metric("Budget capital",fmt(budget["capital"]))
    if query("SELECT id FROM expenses WHERE user_id=?",(uid,)).empty and query("SELECT id FROM income WHERE user_id=?",(uid,)).empty:
        st.info("Insufficient data for a meaningful farm profit/loss. Add expenses and harvest income to begin.")
    st.metric("Farm records", len(farms))
    st.subheader("Quick access")
    a,b,c,d = st.columns(4)
    if a.button("➕ Add expense", use_container_width=True): st.session_state.quick_page="Farm Expenses and Profit Tracker"; st.rerun()
    if b.button("💰 Add harvest income", use_container_width=True): st.session_state.quick_page="Farm Expenses and Profit Tracker"; st.rerun()
    if c.button("📋 Plan budget", use_container_width=True): st.session_state.quick_page="CornCost Planner"; st.rerun()
    if d.button("📈 Check prices", use_container_width=True): st.session_state.quick_page="CornPrice Watch"; st.rerun()
    tx = query("""SELECT date, 'Expense' type, description, amount FROM expenses WHERE user_id=?
        UNION ALL SELECT date, 'Income' type, COALESCE(buyer,'Harvest sale'), gross_sales+other_income amount FROM income WHERE user_id=?
        ORDER BY date DESC LIMIT 10""",(uid,uid))
    st.subheader("Recent transactions")
    show_df(tx)
    if not query("SELECT id FROM price_reports WHERE user_id=?",(uid,)).empty:
        st.subheader("Recent supply prices")
        show_df(query("SELECT product,category,price,unit,supplier,location,reported_at,verification FROM price_reports WHERE user_id=? ORDER BY reported_at DESC LIMIT 5",(uid,)))
    if not query("SELECT id FROM buyer_offers WHERE user_id=?",(uid,)).empty:
        st.subheader("Recent buyer offers")
        show_df(query("SELECT buyer,location,price_per_kg,min_kg,max_kg,updated_at,verification FROM buyer_offers WHERE user_id=? ORDER BY updated_at DESC LIMIT 5",(uid,)))
    if "quick_page" in st.session_state:
        st.info(f"Use the sidebar to open {st.session_state.quick_page}.")
        del st.session_state["quick_page"]

elif page == "Farm Expenses and Profit Tracker":
    st.title("Farm Expenses and Profit Tracker")
    with st.expander("Create a farm record / production cycle", expanded=farms.empty):
        with st.form("farm_add"):
            name=st.text_input("Farm or cycle name*")
            crop=st.text_input("Crop type", "Corn")
            c1,c2=st.columns(2); planting=c1.date_input("Planting date", value=date.today()); harvest=c2.date_input("Expected / actual harvest date", value=None)
            location=st.text_input("General farm location")
            c1,c2,c3=st.columns(3); area=c1.number_input("Area planted (ha)",min_value=0.0,step=.1); expected=c2.number_input("Expected harvest (kg)",min_value=0.0,step=100.0); actual=c3.number_input("Actual harvest (kg)",min_value=0.0,step=100.0)
            status=st.selectbox("Status",["planned","ongoing","harvested","completed"])
            notes=st.text_area("Notes")
            submit=st.form_submit_button("Save farm record")
        if submit:
            if not name.strip(): st.error("Farm/cycle name is required.")
            else:
                execute("INSERT INTO farm_records(user_id,name,crop_type,planting_date,harvest_date,location,area_ha,expected_kg,actual_kg,notes,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (uid,name.strip(),crop,str(planting),str(harvest) if harvest else None,location,area,expected,actual,notes,status,now_text()))
                st.success("Farm record saved."); st.rerun()
    farms=farm_options(uid); farm_labels={int(r.id):r.name for r in farms.itertuples()} if not farms.empty else {}
    if not farms.empty:
        with st.expander("Edit or delete a farm record"):
            choice=st.selectbox("Select record",list(farm_labels),format_func=lambda x:f"{x} — {farm_labels[x]}")
            row=query("SELECT * FROM farm_records WHERE id=? AND user_id=?",(choice,uid)).iloc[0]
            with st.form("farm_edit"):
                ename=st.text_input("Name",row["name"]); elocation=st.text_input("Location",row["location"] or "")
                estatus=st.selectbox("Status",["planned","ongoing","harvested","completed"],index=["planned","ongoing","harvested","completed"].index(row["status"]))
                enotes=st.text_area("Notes",row["notes"] or "")
                save=st.form_submit_button("Update record")
            if save:
                execute("UPDATE farm_records SET name=?,location=?,status=?,notes=? WHERE id=? AND user_id=?",(ename,elocation,estatus,enotes,choice,uid)); st.success("Updated."); st.rerun()
            st.warning("Deleting a farm record is blocked if expenses/income reference it. Reassign or remove those transactions first.")
            confirm=st.checkbox("I understand this deletion cannot be undone",key=f"del_farm_{choice}")
            if st.button("Delete farm record",disabled=not confirm):
                refs=query("SELECT (SELECT COUNT(*) FROM expenses WHERE farm_id=?)+(SELECT COUNT(*) FROM income WHERE farm_id=?) n",(choice,choice)).iloc[0]["n"]
                if refs: st.error("This record has linked transactions. Delete/reassign those transactions first.")
                else:
                    execute("DELETE FROM farm_records WHERE id=? AND user_id=?",(choice,uid)); st.success("Deleted."); st.rerun()
    st.divider()
    st.subheader("Add expense")
    with st.form("expense_add"):
        c1,c2=st.columns(2); edate=c1.date_input("Expense date",value=date.today()); efarm=c2.selectbox("Farm record",["Unassigned"]+[f"{i} — {n}" for i,n in farm_labels.items()])
        c1,c2=st.columns(2); cat=c1.selectbox("Category",EXPENSE_CATEGORIES); desc=c2.text_input("Description*")
        c1,c2,c3=st.columns(3); qty=c1.number_input("Quantity (0 if direct amount)",min_value=0.0); unit=c2.selectbox("Unit",UNITS); unitprice=c3.number_input("Unit price (₱)",min_value=0.0)
        direct=st.number_input("Direct total amount (used when quantity is 0)",min_value=0.0)
        supplier=st.text_input("Supplier"); enotes=st.text_input("Notes")
        submit=st.form_submit_button("Save expense")
    if submit:
        if not desc.strip(): st.error("Description is required.")
        else:
            amount=qty*unitprice if qty>0 else direct
            execute("INSERT INTO expenses(user_id,farm_id,date,category,description,quantity,unit,unit_price,amount,supplier,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (uid,selected_farm(efarm),str(edate),cat,desc,qty if qty else None,unit,unitprice if qty else None,round(amount,2),supplier,enotes))
            st.success(f"Expense saved: {fmt(amount)}"); st.rerun()
    st.subheader("Add harvest income")
    with st.form("income_add"):
        c1,c2=st.columns(2); idate=c1.date_input("Sale date",value=date.today()); ifarm=c2.selectbox("Farm record",["Unassigned"]+[f"{i} — {n}" for i,n in farm_labels.items()],key="income_farm")
        c1,c2,c3=st.columns(3); kg=c1.number_input("Quantity sold (kg)",min_value=0.0); price=c2.number_input("Selling price (₱/kg)",min_value=0.0); other=c3.number_input("Other income / adjustment (₱)",min_value=0.0)
        buyer=st.text_input("Buyer name"); inotes=st.text_input("Income notes")
        submit=st.form_submit_button("Save harvest income")
    if submit:
        gross=kg*price
        if kg<=0 and other<=0: st.error("Enter a positive sale quantity or other income.")
        else:
            execute("INSERT INTO income(user_id,farm_id,date,quantity_kg,price_per_kg,gross_sales,other_income,buyer,notes) VALUES(?,?,?,?,?,?,?,?,?)",
                    (uid,selected_farm(ifarm),str(idate),kg,price,round(gross,2),other,buyer,inotes))
            st.success(f"Income saved. Gross sales: {fmt(gross)}"); st.rerun()
    st.divider()
    st.subheader("Financial summary and transactions")
    filter_farm=st.selectbox("Filter by farm",["All"]+[f"{i} — {n}" for i,n in farm_labels.items()],key="filter_farm")
    farm_id=selected_farm(filter_farm) if filter_farm!="All" else None
    exsql="SELECT * FROM expenses WHERE user_id=?"; insql="SELECT * FROM income WHERE user_id=?"; args=[uid]
    if farm_id:
        exsql+=" AND farm_id=?"; insql+=" AND farm_id=?"; args.append(farm_id)
    ex=query(exsql+" ORDER BY date DESC",tuple(args)); incdf=query(insql+" ORDER BY date DESC",tuple(args))
    totalex=float(ex["amount"].sum()) if not ex.empty else 0
    totalinc=float((incdf["gross_sales"]+incdf["other_income"]).sum()) if not incdf.empty else 0
    a,b,c=st.columns(3); a.metric("Total expenses",fmt(totalex)); b.metric("Total income",fmt(totalinc)); c.metric("Profit / loss",fmt(totalinc-totalex))
    if ex.empty and incdf.empty: st.info("Insufficient data: record at least one expense or income transaction.")
    if not ex.empty:
        st.subheader("Expenses by category")
        chart=ex.groupby("category",as_index=False)["amount"].sum()
        st.plotly_chart(px.bar(chart,x="category",y="amount",title="Recorded expenses by category"),use_container_width=True)
    if not ex.empty or not incdf.empty:
        trend=[]
        if not ex.empty:
            z=ex.groupby("date",as_index=False)["amount"].sum(); z["type"]="Expenses"; z=z.rename(columns={"amount":"value"}); trend.append(z)
        if not incdf.empty:
            z=incdf.groupby("date",as_index=False).apply(lambda x: pd.Series({"value":(x.gross_sales+x.other_income).sum()})).reset_index(drop=True); z["type"]="Income"; trend.append(z)
        t=pd.concat(trend,ignore_index=True); st.plotly_chart(px.line(t,x="date",y="value",color="type",markers=True,title="Income and expense trend"),use_container_width=True)
    st.subheader("Expense history")
    show_df(ex[["id","date","category","description","amount","supplier","farm_id"]] if not ex.empty else ex)
    if not ex.empty:
        with st.expander("Delete an expense (confirmation required)"):
            eid=st.selectbox("Expense ID",ex.id.tolist())
            if st.button("Delete selected expense",key="delete_expense"):
                if st.checkbox("Confirm permanent deletion",key="confirm_del_exp"):
                    execute("DELETE FROM expenses WHERE id=? AND user_id=?",(eid,uid)); st.success("Expense deleted."); st.rerun()
    st.subheader("Income history")
    show_df(incdf[["id","date","quantity_kg","price_per_kg","gross_sales","other_income","buyer","farm_id"]] if not incdf.empty else incdf)
    csvdf=pd.concat([ex.assign(transaction_type="Expense"),incdf.assign(transaction_type="Income")],ignore_index=True,sort=False)
    if not csvdf.empty: st.download_button("Export transactions CSV",csvdf.to_csv(index=False).encode("utf-8"),"cornprofit_transactions.csv","text/csv")

elif page == "CornCost Planner":
    st.title("CornCost Planner")
    if farms.empty: st.warning("Create a farm record first in Farm Expenses and Profit Tracker.")
    else:
        with st.form("budget_create"):
            farm_label=st.selectbox("Farm cycle",[f"{i} — {n}" for i,n in farm_labels.items()])
            bname=st.text_input("Budget name","Planting budget")
            c1,c2=st.columns(2); capital=c1.number_input("Available capital (₱)",min_value=0.0); emergency=c2.number_input("Emergency allowance (₱)",min_value=0.0)
            c1,c2=st.columns(2); expectedkg=c1.number_input("Expected saleable harvest (kg)",min_value=0.0); expectedprice=c2.number_input("Expected selling price (₱/kg)",min_value=0.0)
            st.caption("Enter planned totals by category. Quantity and unit cost are stored for reference.")
            items=[]
            cols=st.columns(2)
            for idx,cat in enumerate(BUDGET_CATEGORIES):
                with cols[idx%2]:
                    st.markdown(f"**{cat}**")
                    q=st.number_input(f"{cat} quantity",min_value=0.0,key=f"bq_{cat}")
                    unit=st.selectbox(f"{cat} unit",UNITS,key=f"bu_{cat}")
                    cost=st.number_input(f"{cat} estimated unit cost (₱)",min_value=0.0,key=f"bc_{cat}")
                    items.append((cat,q,unit,cost,q*cost))
            submit=st.form_submit_button("Save budget")
        if submit:
            total=sum(x[4] for x in items)+emergency
            with db() as con:
                cur=con.execute("INSERT INTO budgets(user_id,farm_id,name,capital,emergency_allowance,expected_kg,expected_price,created_at) VALUES(?,?,?,?,?,?,?,?)",
                                (uid,selected_farm(farm_label),bname,capital,emergency,expectedkg,expectedprice,now_text()))
                bid=cur.lastrowid
                for cat,q,u,cost,totalitem in items:
                    if q or cost:
                        con.execute("INSERT INTO budget_items(budget_id,category,quantity,unit,unit_cost,total) VALUES(?,?,?,?,?,?)",(bid,cat,q,u,cost,totalitem))
            st.success(f"Budget saved. Planned costs including emergency allowance: {fmt(total)}"); st.rerun()
        budgets=query("SELECT * FROM budgets WHERE user_id=? ORDER BY id DESC",(uid,))
        st.subheader("Saved budgets")
        show_df(budgets)
        if not budgets.empty:
            bid=st.selectbox("Choose budget to analyze",budgets.id.tolist(),format_func=lambda x:f"{x} — {budgets[budgets.id==x].iloc[0]['name']}")
            b=budgets[budgets.id==bid].iloc[0]
            bi=query("SELECT * FROM budget_items WHERE budget_id=?",(bid,))
            planned=float(bi.total.sum()) if not bi.empty else 0
            planned_with_emergency=planned+float(b.emergency_allowance)
            shortage=max(0,planned_with_emergency-float(b.capital))
            a,c,d=st.columns(3); a.metric("Planned costs",fmt(planned_with_emergency)); c.metric("Capital remaining",fmt(float(b.capital)-planned_with_emergency)); d.metric("Funding shortage",fmt(shortage))
            if shortage>0: st.warning(f"Planned costs exceed capital by {fmt(shortage)}.")
            else: st.success("Available capital covers the planned amount entered.")
            be=break_even_price(planned_with_emergency,b.expected_kg)
            st.metric("Estimated break-even price",fmt(be) + "/kg" if be is not None else "Insufficient data")
            rev=estimated_revenue(b.expected_kg,b.expected_price)
            st.metric("Estimated revenue",fmt(rev)); st.metric("Estimated profit/loss",fmt(float(rev)-planned_with_emergency))
            if be is None: st.warning("Enter a positive expected saleable harvest quantity to calculate break-even price.")
            st.caption("Forecast only. Actual harvest, quality deductions, market price, and costs can differ.")
            actual=query("SELECT category, SUM(amount) actual FROM expenses WHERE user_id=? AND farm_id=? GROUP BY category",(uid,int(b.farm_id))) if b.farm_id else pd.DataFrame()
            if not bi.empty:
                comparison=bi.groupby("category",as_index=False)["total"].sum().rename(columns={"total":"planned"})
                if not actual.empty: comparison=comparison.merge(actual,on="category",how="left")
                else: comparison["actual"]=0
                comparison["actual"]=comparison["actual"].fillna(0)
                comparison["difference (actual - planned)"]=comparison["actual"]-comparison["planned"]
                comparison["% over/under"]=comparison.apply(lambda r: ((r["actual"]-r["planned"])/r["planned"]*100) if r["planned"] else None,axis=1)
                st.subheader("Planned versus actual")
                show_df(comparison)
                st.plotly_chart(px.bar(comparison,x="category",y=["planned","actual"],barmode="group",title="Budget versus actual"),use_container_width=True)

elif page == "CornPrice Watch":
    st.title("CornPrice Watch")
    st.caption("Manual reports only unless you import a trusted file. No live government or supplier feed is connected.")
    with st.expander("Add supply price report",expanded=True):
        with st.form("price_add"):
            c1,c2=st.columns(2); product= c1.text_input("Product name*"); category=c2.selectbox("Category",PRICE_CATEGORIES)
            c1,c2,c3=st.columns(3); brand=c1.text_input("Brand"); size=c2.number_input("Package size",min_value=0.001,value=1.0); unit=c3.selectbox("Package unit",["kg","g","L","mL","bag","sack","piece"])
            c1,c2=st.columns(2); price=c1.number_input("Price (₱)",min_value=0.0); supplier=c2.text_input("Supplier/source")
            location=st.text_input("Municipality / region"); verified=c1.selectbox("Verification status",["Unverified","Verified by reporting process","Expired / stale"])
            notes=st.text_area("Notes / conditions")
            submit=st.form_submit_button("Save price report")
        if submit:
            if not product.strip(): st.error("Product name is required.")
            else:
                execute("INSERT INTO price_reports(user_id,product,category,brand,package_size,unit,price,supplier,location,reported_at,verification,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (uid,product,category,brand,size,unit,price,supplier,location,now_text(),verified,notes))
                st.success("Price report saved."); st.rerun()
    with st.expander("Import price reports from CSV"):
        st.write("Expected columns: product, category, price. Optional: brand, package_size, unit, supplier, location, verification, notes.")
        uploaded=st.file_uploader("Choose CSV",type=["csv"],key="price_csv")
        if uploaded and st.button("Import CSV"):
            try:
                df=pd.read_csv(uploaded)
                if not {"product","category","price"}.issubset(df.columns): raise ValueError("CSV must contain product, category, and price columns.")
                count=0
                for _,r in df.iterrows():
                    if pd.isna(r["product"]) or pd.isna(r["category"]) or float(r["price"])<0: continue
                    execute("INSERT INTO price_reports(user_id,product,category,brand,package_size,unit,price,supplier,location,reported_at,verification,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (uid,str(r["product"]),str(r["category"]),str(r.get("brand","")),float(r.get("package_size",1) or 1),str(r.get("unit","kg")),float(r["price"]),str(r.get("supplier","")),str(r.get("location","")),now_text(),str(r.get("verification","Unverified")),str(r.get("notes",""))))
                    count+=1
                st.success(f"Imported {count} price reports."); st.rerun()
            except Exception as e: st.error(f"CSV import failed: {e}")
    prices=query("SELECT * FROM price_reports WHERE user_id=? ORDER BY reported_at DESC",(uid,))
    st.subheader("Price listings and filters")
    if not prices.empty:
        c1,c2,c3=st.columns(3); catf=c1.selectbox("Category filter",["All"]+sorted(prices.category.dropna().unique().tolist())); locf=c2.text_input("Location contains"); prod_f=c3.text_input("Product contains")
        low,high=st.columns(2); minp=low.number_input("Minimum price",min_value=0.0,value=0.0); maxp=high.number_input("Maximum price (0 = no limit)",min_value=0.0,value=0.0)
        filt=prices.copy()
        if catf!="All": filt=filt[filt.category==catf]
        if locf: filt=filt.location.fillna("").str.contains(locf,case=False)
        if prod_f: filt=filt.product.str.contains(prod_f,case=False)
        filt=filt[filt.price>=minp]
        if maxp>0: filt=filt[filt.price<=maxp]
        sort=st.selectbox("Sort",["Newest report","Lowest price","Highest price"])
        if sort=="Lowest price": filt=filt.sort_values("price")
        elif sort=="Highest price": filt=filt.sort_values("price",ascending=False)
        else: filt=filt.sort_values("reported_at",ascending=False)
        filt["comparable unit price"] = filt.apply(lambda r: float(r.price)/float(r.package_size) if r.package_size and r.unit in ["kg","L"] else None,axis=1)
        show_df(filt[["id","product","category","brand","package_size","unit","price","comparable unit price","supplier","location","reported_at","verification","notes"]])
        st.caption("Comparable unit price is shown only for kg/L packages. Different units and package definitions should not be compared directly.")
        st.subheader("Set target-price alert")
        with st.form("price_alert"):
            ap=st.text_input("Product name")
            target=st.number_input("Alert when price is at or below (₱)",min_value=0.0)
            save=st.form_submit_button("Save alert")
        if save and ap.strip():
            execute("INSERT INTO price_alerts(user_id,product,target_price,condition,active) VALUES(?,?,?,?,1)",(uid,ap.strip(),target,"at or below")); st.success("In-app alert saved.")
        alerts=query("SELECT * FROM price_alerts WHERE user_id=? AND active=1",(uid,))
        for _,a in alerts.iterrows():
            matches=prices[(prices.product.str.lower()==str(a.product).lower())&(prices.price<=a.target_price)]
            if not matches.empty: st.warning(f"Price alert: {a.product} has a report at or below {fmt(a.target_price)}. Check the report date and verification.")
        st.subheader("Edit / verify your report")
        rid=st.selectbox("Report ID",prices.id.tolist())
        with st.form("price_edit"):
            new_status=st.selectbox("Verification status",["Unverified","Verified by reporting process","Expired / stale"])
            new_notes=st.text_input("Updated notes",str(prices[prices.id==rid].iloc[0].notes or ""))
            save=st.form_submit_button("Update report status")
        if save:
            execute("UPDATE price_reports SET verification=?,notes=? WHERE id=? AND user_id=?",(new_status,new_notes,rid,uid)); st.success("Report updated."); st.rerun()
        if len(prices)>=2:
            st.subheader("Price history")
            trend=prices.copy(); trend["reported_at"]=pd.to_datetime(trend.reported_at,errors="coerce")
            st.plotly_chart(px.line(trend,x="reported_at",y="price",color="product",markers=True,title="Entered price reports over time"),use_container_width=True)
        st.download_button("Export price reports CSV",prices.to_csv(index=False).encode(), "cornprice_reports.csv","text/csv")
    else: st.info("No supply prices yet. Add a report or import a CSV. No live prices are connected.")

elif page == "CornBulk Connect":
    st.title("CornBulk Connect")
    tab1,tab2,tab3,tab4=st.tabs(["Find Other Farmers","Buyers Available","Compare Offers","Group Selling"])
    with tab1:
        st.subheader("Create a farmer listing")
        with st.form("farmer_listing"):
            display=st.text_input("Public display name",user["full_name"])
            location=st.text_input("General location (no home address)")
            qty=st.number_input("Expected harvest quantity (kg)",min_value=0.0)
            harvest=date_input=date.today()
            hdate=st.date_input("Expected harvest date",value=date.today())
            arrangement=st.selectbox("Preferred selling arrangement",["Individual sale","Group selling","Open to either"])
            quality=st.text_input("Corn quality information (optional)")
            contact=st.text_input("Optional public contact method")
            submit=st.form_submit_button("Publish listing")
        if submit:
            execute("INSERT INTO farmer_listings(user_id,display_name,location,expected_kg,harvest_date,arrangement,quality,contact,status,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (uid,display,location,qty,str(hdate),arrangement,quality,contact,"Open",now_text()))
            st.success("Farmer listing published."); st.rerun()
        listings=query("SELECT * FROM farmer_listings WHERE status='Open' ORDER BY updated_at DESC")
        show_df(listings[["id","display_name","location","expected_kg","harvest_date","arrangement","quality","updated_at"]] if not listings.empty else listings)
        if not listings.empty:
            listing_id=st.selectbox("Choose a farmer listing to request connection",listings.id.tolist())
            target_user=int(listings[listings.id==listing_id].iloc[0].user_id)
            if target_user==uid: st.caption("This is your own listing.")
            elif st.button("Request to Connect"):
                execute("INSERT INTO connection_requests(from_user,to_user,listing_id,status,created_at) VALUES(?,?,?,?,?)",(uid,target_user,listing_id,"Pending",now_text()))
                st.success("Connection request recorded in the prototype."); st.rerun()
        st.subheader("Connection requests")
        req=query("""SELECT cr.id, u.full_name as other_farmer, cr.status, cr.created_at, cr.from_user, cr.to_user
            FROM connection_requests cr JOIN users u ON u.id=CASE WHEN cr.from_user=? THEN cr.to_user ELSE cr.from_user END
            WHERE cr.from_user=? OR cr.to_user=? ORDER BY cr.id DESC""",(uid,uid,uid))
        show_df(req[["id","other_farmer","status","created_at"]] if not req.empty else req)
        if not req.empty:
            pending=req[req.to_user==uid]
            if not pending.empty:
                rid=st.selectbox("Incoming request ID",pending.id.tolist())
                status=st.selectbox("Respond",["Accepted","Declined"])
                if st.button("Save response"): execute("UPDATE connection_requests SET status=? WHERE id=? AND to_user=?",(status,rid,uid)); st.success("Response saved."); st.rerun()
    with tab2:
        st.subheader("Add buyer offer")
        with st.form("buyer_add"):
            buyer=st.text_input("Buyer / business name*")
            loc=st.text_input("General pickup / business location")
            c1,c2,c3=st.columns(3); price=c1.number_input("Offer price (₱/kg)",min_value=0.0); minq=c2.number_input("Minimum quantity (kg)",min_value=0.0); maxq=c3.number_input("Maximum quantity (kg; 0 unknown)",min_value=0.0)
            corn=st.text_input("Corn type / quality requirements"); moisture=st.text_input("Moisture requirement")
            c1,c2=st.columns(2); fixed=c1.number_input("Fixed deduction (₱; if stated)",min_value=0.0); pct=c2.number_input("Percentage deduction (%)",min_value=0.0,max_value=100.0)
            terms=st.text_input("Payment terms"); delivery=st.text_input("Pickup / delivery requirements"); expires=st.date_input("Offer expiration date",value=date.today())
            contact=st.text_input("Contact information"); verification=st.selectbox("Status",["Unverified","Verified by reporting process","Expired / stale"]); notes=st.text_area("Other notes / deductions")
            submit=st.form_submit_button("Save buyer offer")
        if submit:
            if not buyer.strip(): st.error("Buyer name is required.")
            else:
                execute("INSERT INTO buyer_offers(user_id,buyer,location,price_per_kg,min_kg,max_kg,corn_type,moisture,fixed_deduction,percent_deduction,payment_terms,delivery,expires,updated_at,verification,contact,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (uid,buyer,loc,price,minq,maxq,corn,moisture,fixed,pct,terms,delivery,str(expires),now_text(),verification,contact,notes))
                st.success("Offer saved."); st.rerun()
        offers=query("SELECT * FROM buyer_offers ORDER BY updated_at DESC")
        if not offers.empty:
            c1,c2=st.columns(2); loc_filter=c1.text_input("Filter buyer location"); minprice=c2.number_input("Minimum offer price",min_value=0.0,value=0.0)
            filt=offers[offers.price_per_kg>=minprice]
            if loc_filter: filt=filt[filt.location.fillna("").str.contains(loc_filter,case=False)]
            show_df(filt[["id","buyer","location","price_per_kg","min_kg","max_kg","corn_type","moisture","payment_terms","expires","updated_at","verification"]])
            offer_id=st.selectbox("Select offer to view / save / contact",filt.id.tolist() if not filt.empty else offers.id.tolist())
            offer=offers[offers.id==offer_id].iloc[0]
            with st.expander("View offer details",expanded=True):
                for k in ["buyer","location","price_per_kg","min_kg","max_kg","corn_type","moisture","fixed_deduction","percent_deduction","payment_terms","delivery","expires","updated_at","verification","contact","notes"]:
                    st.write(f"**{k.replace('_',' ').title()}:** {offer[k]}")
                saved=query("SELECT * FROM saved_offers WHERE user_id=? AND offer_id=?",(uid,offer_id))
                if saved.empty:
                    if st.button("Save offer"): execute("INSERT OR IGNORE INTO saved_offers(user_id,offer_id,contacted) VALUES(?,?,0)",(uid,offer_id)); st.success("Offer saved."); st.rerun()
                else:
                    st.success("Offer is saved.")
                    if st.button("Remove saved offer"): execute("DELETE FROM saved_offers WHERE user_id=? AND offer_id=?",(uid,offer_id)); st.success("Removed."); st.rerun()
                    if st.button("Record that I contacted buyer"): execute("UPDATE saved_offers SET contacted=1 WHERE user_id=? AND offer_id=?",(uid,offer_id)); st.success("Contact status recorded (no message was sent)."); st.rerun()
            st.markdown("#### Location and transport estimate")
            st.caption("No map API is configured. Enter a manually estimated round-trip distance; this is not a road-route result.")
            with st.form("transport"):
                distance=st.number_input("Round-trip distance (km)",min_value=0.0)
                lpkm=st.number_input("Fuel consumption (liters/km)",min_value=0.0,value=.1,format="%.3f")
                fuelprice=st.number_input("Fuel price (₱/liter)",min_value=0.0)
                loading=st.number_input("Loading / unloading (₱)",min_value=0.0); toll=st.number_input("Tolls (₱)",min_value=0.0); othercost=st.number_input("Other charges (₱)",min_value=0.0)
                hired=st.checkbox("Use quoted hired-vehicle fee instead"); hiredfee=st.number_input("Quoted vehicle fee (₱)",min_value=0.0,disabled=not hired)
                calc=st.form_submit_button("Calculate and save transport estimate")
            if calc:
                fc=fuel_cost(distance,lpkm,fuelprice)
                total=transport_total(fc,loading,toll,othercost,hiredfee if hired else None)
                execute("INSERT INTO transport_estimates(user_id,offer_id,distance_km,liters_per_km,fuel_price,loading,tolls,other,hired_fee,total,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                        (uid,offer_id,distance,lpkm,fuelprice,loading,toll,othercost,hiredfee if hired else None,float(total),now_text()))
                st.success(f"Fuel cost = distance × L/km × fuel price = {fmt(fc)}. Estimated transport total = {fmt(total)}. " + ("Quoted vehicle fee replaces fuel/vehicle and other entered costs." if hired else "Includes fuel, loading, tolls and other costs."))
                st.rerun()
    with tab3:
        st.subheader("Compare buyer offers")
        offers=query("SELECT * FROM buyer_offers ORDER BY updated_at DESC")
        if offers.empty: st.info("Add buyer offers first.")
        else:
            ids=st.multiselect("Choose two or more offers",offers.id.tolist(),format_func=lambda x:f"{x} — {offers[offers.id==x].iloc[0]['buyer']} ({fmt(offers[offers.id==x].iloc[0]['price_per_kg'])}/kg)")
            quantity=st.number_input("Quantity to sell (kg)",min_value=0.0)
            if ids and quantity>0:
                results=[]
                for oid in ids:
                    o=offers[offers.id==oid].iloc[0]
                    ts=query("SELECT total FROM transport_estimates WHERE user_id=? AND offer_id=? ORDER BY id DESC LIMIT 1",(uid,oid))
                    transport=float(ts.iloc[0]["total"]) if not ts.empty else 0
                    gross=buyer_gross(quantity,o.price_per_kg)
                    net=buyer_net(quantity,o.price_per_kg,transport,o.fixed_deduction,o.percent_deduction)
                    results.append({"Buyer":o.buyer,"Offer (₱/kg)":o.price_per_kg,"Quantity (kg)":quantity,"Gross revenue":float(gross),"Transport estimate":transport,"Fixed deduction":o.fixed_deduction,"Percentage deduction":o.percent_deduction,"Estimated net proceeds":float(net),"Minimum kg":o.min_kg,"Maximum kg":o.max_kg,"Terms":o.payment_terms,"Quality":o.corn_type,"Updated":o.updated_at,"Verification":o.verification})
                resultdf=pd.DataFrame(results).sort_values("Estimated net proceeds",ascending=False)
                show_df(resultdf)
                st.success(f"Highest estimated net proceeds: {resultdf.iloc[0]['Buyer']} — {fmt(resultdf.iloc[0]['Estimated net proceeds'])}. Estimates exclude production costs.")
                st.caption("A saved transport estimate is used if one exists; otherwise transport is treated as ₱0 and must be entered before relying on the comparison. Confirm all offer terms directly.")
    with tab4:
        st.subheader("Group-selling plan and cost sharing")
        with st.form("group_plan"):
            name=st.text_input("Plan name")
            target=st.text_input("Target buyer")
            gprice=st.number_input("Expected selling price (₱/kg)",min_value=0.0)
            shared=st.number_input("Shared transportation cost (₱)",min_value=0.0)
            terms=st.text_input("Payment terms")
            quality=st.text_input("Quality requirements")
            n=st.number_input("Number of participating farmers",min_value=1,max_value=20,value=3)
            members=[]
            for i in range(int(n)):
                c1,c2,c3=st.columns(3)
                nm=c1.text_input(f"Farmer {i+1} name",key=f"gm_name_{i}")
                q=c2.number_input(f"Farmer {i+1} quantity (kg)",min_value=0.0,key=f"gm_qty_{i}")
                agreed=c3.checkbox("Agreed to join",key=f"gm_agree_{i}")
                members.append((nm or f"Member {i+1}",q,agreed))
            method=st.selectbox("Cost-sharing method",["Proportional to quantity","Equal sharing","Custom agreed amounts"])
            custom=[]
            if method=="Custom agreed amounts":
                for i in range(int(n)): custom.append(st.number_input(f"Custom cost for {members[i][0]}",min_value=0.0,key=f"custom_{i}"))
            submit=st.form_submit_button("Calculate and save group plan")
        if submit:
            if not name.strip(): st.error("Plan name is required.")
            elif any(not m[2] for m in members): st.error("Each participating farmer must explicitly confirm agreement before saving.")
            else:
                try:
                    alloc=allocate_shared_cost(shared,[m[1] for m in members],method,custom if method=="Custom agreed amounts" else None)
                    with db() as con:
                        cur=con.execute("INSERT INTO group_plans(user_id,name,buyer,price_per_kg,transport_cost,payment_terms,quality_requirements,created_at) VALUES(?,?,?,?,?,?,?,?)",(uid,name,target,gprice,shared,terms,quality,now_text()))
                        pid=cur.lastrowid
                        for m,cost in zip(members,alloc):
                            proceeds=float(buyer_gross(m[1],gprice))-float(cost)
                            con.execute("INSERT INTO group_members(plan_id,farmer_name,quantity_kg,agreed) VALUES(?,?,?,1)",(pid,m[0],m[1]))
                            con.execute("INSERT INTO cost_allocations(plan_id,farmer_name,quantity_kg,assigned_cost,proceeds) VALUES(?,?,?,?,?)",(pid,m[0],m[1],float(cost),proceeds))
                    st.success(f"Plan saved. Combined quantity: {fmt(group_quantity([m[1] for m in members]))} kg. Allocated cost: {fmt(sum(alloc))}.")
                    st.rerun()
                except Exception as e: st.error(f"Could not allocate costs: {e}")
        plans=query("SELECT * FROM group_plans WHERE user_id=? ORDER BY id DESC",(uid,))
        show_df(plans)
        if not plans.empty:
            pid=st.selectbox("View saved plan",plans.id.tolist())
            allocations=query("SELECT farmer_name,quantity_kg,assigned_cost,proceeds FROM cost_allocations WHERE plan_id=?",(pid,))
            show_df(allocations)
            if not allocations.empty: st.metric("Combined harvest quantity",f"{allocations.quantity_kg.sum():,.2f} kg")

elif page == "Farm Records":
    st.title("Farm Records")
    farms=farm_options(uid)
    if farms.empty: st.info("No farm records yet.")
    else:
        c1,c2=st.columns(2); search=c1.text_input("Search farm name or location"); statusf=c2.selectbox("Status",["All","planned","ongoing","harvested","completed"])
        f=query("SELECT * FROM farm_records WHERE user_id=? ORDER BY id DESC",(uid,))
        if search: f=f[f.name.fillna("").str.contains(search,case=False)|f.location.fillna("").str.contains(search,case=False)]
        if statusf!="All": f=f[f.status==statusf]
        show_df(f)
        if not f.empty:
            fid=st.selectbox("Open farm record",f.id.tolist(),format_func=lambda x:f"{x} — {f[f.id==x].iloc[0]['name']}")
            st.subheader("Associated expenses")
            show_df(query("SELECT date,category,description,amount FROM expenses WHERE user_id=? AND farm_id=? ORDER BY date DESC",(uid,fid)))
            st.subheader("Associated income")
            show_df(query("SELECT date,quantity_kg,price_per_kg,gross_sales,other_income,buyer FROM income WHERE user_id=? AND farm_id=? ORDER BY date DESC",(uid,fid)))
            st.subheader("Budget plans")
            show_df(query("SELECT id,name,capital,emergency_allowance,expected_kg,expected_price FROM budgets WHERE user_id=? AND farm_id=?",(uid,fid)))
            export=query("""SELECT date,'Expense' type,category description,amount FROM expenses WHERE user_id=? AND farm_id=?
                UNION ALL SELECT date,'Income' type,COALESCE(buyer,'Harvest sale'),gross_sales+other_income FROM income WHERE user_id=? AND farm_id=? ORDER BY date""",(uid,fid,uid,fid))
            if not export.empty: st.download_button("Export this farm's transactions",export.to_csv(index=False).encode(),"farm_transactions.csv","text/csv")

elif page == "Community":
    st.title("Community")
    st.write("Community interactions here are stored in this local prototype; no external farmer network is connected.")
    st.subheader("Your listings")
    show_df(query("SELECT id,display_name,location,expected_kg,harvest_date,arrangement,status,updated_at FROM farmer_listings WHERE user_id=? ORDER BY id DESC",(uid,)))
    st.subheader("Your connection requests")
    show_df(query("""SELECT id,from_user,to_user,status,created_at FROM connection_requests WHERE from_user=? OR to_user=? ORDER BY id DESC""",(uid,uid)))
    st.subheader("Saved buyer offers")
    show_df(query("""SELECT b.id,b.buyer,b.location,b.price_per_kg,b.updated_at,b.verification,s.contacted
        FROM saved_offers s JOIN buyer_offers b ON b.id=s.offer_id WHERE s.user_id=? ORDER BY b.updated_at DESC""",(uid,)))
    st.subheader("Group selling plans")
    show_df(query("SELECT id,name,buyer,price_per_kg,transport_cost,payment_terms,created_at FROM group_plans WHERE user_id=? ORDER BY id DESC",(uid,)))

elif page == "Profile":
    st.title("Profile")
    with st.form("profile"):
        name=st.text_input("Full name",user["full_name"])
        contact=st.text_input("Email or phone",user["contact"])
        municipality=st.text_input("Municipality",user["municipality"] or "")
        barangay=st.text_input("Barangay",user["barangay"] or "")
        farm=st.text_input("Farm name",user["farm_name"] or "")
        save=st.form_submit_button("Save profile")
    if save:
        try:
            execute("UPDATE users SET full_name=?,contact=?,municipality=?,barangay=?,farm_name=? WHERE id=?",(name,contact.lower(),municipality,barangay,farm,uid))
            st.success("Profile updated."); st.rerun()
        except Exception as e: st.error(f"Could not update profile. Contact may already be used. {e}")
    st.caption("Only general location should be used in public farmer listings. Avoid publishing a home address.")

elif page == "Settings":
    st.title("Settings")
    st.subheader("Preferences")
    st.write("Currency: Philippine peso (₱). Units: kg, metric tons, liters, kilometers. These are the prototype defaults.")
    st.subheader("Data export")
    all_exp=query("SELECT * FROM expenses WHERE user_id=?",(uid,)); all_inc=query("SELECT * FROM income WHERE user_id=?",(uid,))
    c1,c2=st.columns(2)
    c1.download_button("Download expenses CSV",all_exp.to_csv(index=False).encode(),"expenses.csv","text/csv")
    c2.download_button("Download income CSV",all_inc.to_csv(index=False).encode(),"income.csv","text/csv")
    st.subheader("Sample-data management")
    st.warning("Demo data is fictional and must not be used for real farm decisions.")
    if st.button("Load demonstration data"):
        add_demo(uid); st.success("Demonstration records added and labelled."); st.rerun()
    st.subheader("Application and privacy")
    st.write("Core recordkeeping and calculations run locally/offline. Live supply prices, online maps, route time, cloud backup, remote multi-user sync, and real messages/notifications are not configured.")
    st.write("Password hashes use PBKDF2. This is a student prototype, not audited for public commercial use. Keep the database private and back it up.")
    st.write("Estimates depend on the accuracy of entered information. CornProfit Connect cannot guarantee profit, buyer purchases, or price accuracy.")
    st.subheader("Help")
    st.markdown("1. Create a farm cycle.\n2. Add expenses and sale income.\n3. Create a budget to estimate break-even price.\n4. Enter local supply prices and buyer offers manually.\n5. Enter round-trip distance to estimate transport.\n6. Compare net proceeds before production costs and confirm offers directly.")
