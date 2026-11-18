"""Observation-only Streamlit dashboard for apex_movement_tracker.py."""
import sqlite3
import time
import pandas as pd
import streamlit as st
from apex_movement_tracker import DB, latest_rows

st.set_page_config(page_title='RADAR APEX | Market Movements',page_icon='📈',layout='wide')
st.title('RADAR APEX | Market Movements')
st.caption('Observed Kraken USD spot price changes — not entry signals or trading recommendations.')
left,right=st.columns(2)
with left:
    window=st.selectbox('Rank by observed window',['5m','15m','1h','4h','24h','1m'],index=1)
with right:
    min_vol=st.number_input('Minimum 24h USD volume',min_value=0, value=250000,step=50000)
try:
    db=sqlite3.connect(f'file:{DB}?mode=ro',uri=True)
    rows=latest_rows(db,min_vol)
    db.close()
except sqlite3.Error:
    rows=[]
if rows:
    df=pd.DataFrame(rows)
    ready=df[df[window].notna()].sort_values(window,ascending=False)
    st.metric('Pairs observed',len(df))
    st.metric('Pairs with complete selected window',len(ready))
    if ready.empty:
        st.info('Collecting historical samples. Selected timeframe is not ready yet.')
    else:
        cols=['pair','price','1m','5m','15m','1h','4h','24h','usd_volume_24h','trend']
        st.dataframe(ready[cols],hide_index=True,use_container_width=True,
                     column_config={**{k:st.column_config.NumberColumn(k,format='%.2f%%') for k in ('1m','5m','15m','1h','4h','24h')},
                                    'price':st.column_config.NumberColumn('Price',format='%.8f'),
                                    'usd_volume_24h':st.column_config.NumberColumn('24h USD Volume',format='$%.0f')})
        st.subheader('Strongest observed upward moves')
        st.bar_chart(ready.head(15).set_index('pair')[window],horizontal=True)
else:
    st.info('No observations yet. Start apex_movement_tracker.py and allow the selected timeframe to build history.')
if st.button('Refresh now'):
    st.rerun()
st.caption('Data is sampled, not tick-by-tick. Missing history is shown as unavailable. 24h volume is a Kraken rolling ticker estimate.')
