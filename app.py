import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# -------------------------
# Page Configuration
# -------------------------
st.set_page_config(
    page_title="Sports Event Manager",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# Custom CSS for better styling
# -------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF6B35;
        text-align: center;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: #2E86AB;
        margin-bottom: 1rem;
        border-left: 4px solid #FF6B35;
        padding-left: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .success-message {
        background: linear-gradient(90deg, #56ab2f, #a8e6cf);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        text-align: center;
        margin: 1rem 0;
    }
    
    .info-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        margin: 1rem 0;
    }
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2E86AB 0%, #A23B72 100%);
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #FF6B35, #F7931E);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .tournament-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 5px solid #FF6B35;
        color: white;
    }
    
    .tournament-card h4 {
        color: #FFE66D;
        margin-bottom: 0.8rem;
        font-weight: bold;
    }
    
    .tournament-card p {
        color: #F0F0F0;
        margin: 0.3rem 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------
# Connect to PostgreSQL DB
# -------------------------
def get_connection():
    return psycopg2.connect(
        host="localhost",
        user="shreyavarma",
        password="441107",
        database="Sports_Event_Tracker"
    )

# -------------------------
# Helper functions
# -------------------------
def get_tournaments():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT tournament_id, name, start_date, end_date FROM Tournaments ORDER BY tournament_id")
        tournaments = cursor.fetchall()
        return tournaments
    finally:
        cursor.close()
        conn.close()

def get_teams(tournament_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT team_id, name FROM Teams WHERE tournament_id=%s ORDER BY team_id", (tournament_id,))
        teams = cursor.fetchall()
        return teams
    finally:
        cursor.close()
        conn.close()

def get_matches():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT m.match_id, t1.name AS team1_name, t2.name AS team2_name, 
                   t.name AS tournament_name, m.match_date, m.team1_score, m.team2_score
            FROM Matches m
            JOIN Teams t1 ON m.team1_id = t1.team_id
            JOIN Teams t2 ON m.team2_id = t2.team_id
            JOIN Tournaments t ON m.tournament_id = t.tournament_id
            ORDER BY m.match_date DESC, m.match_id
        """)
        matches = cursor.fetchall()
        return matches
    finally:
        cursor.close()
        conn.close()

def get_tournament_stats(tournament_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Get team count
        cursor.execute("SELECT COUNT(*) as team_count FROM Teams WHERE tournament_id=%s", (tournament_id,))
        team_count = cursor.fetchone()['team_count']
        
        # Get match count
        cursor.execute("SELECT COUNT(*) as match_count FROM Matches WHERE tournament_id=%s", (tournament_id,))
        match_count = cursor.fetchone()['match_count']
        
        # Get completed matches
        cursor.execute("SELECT COUNT(*) as completed FROM Matches WHERE tournament_id=%s AND team1_score IS NOT NULL", (tournament_id,))
        completed = cursor.fetchone()['completed']
        
        return team_count, match_count, completed
    finally:
        cursor.close()
        conn.close()

# -------------------------
# Insert tournament
# -------------------------
def add_tournament(name, start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Tournaments (name, start_date, end_date) VALUES (%s, %s, %s)",
            (name, start_date, end_date)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# -------------------------
# Delete tournament
# -------------------------
def delete_tournament(tournament_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM Matches WHERE tournament_id=%s", (tournament_id,))
        cursor.execute("DELETE FROM Points_Table WHERE tournament_id=%s", (tournament_id,))
        cursor.execute("DELETE FROM Teams WHERE tournament_id=%s", (tournament_id,))
        cursor.execute("DELETE FROM Tournaments WHERE tournament_id=%s", (tournament_id,))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# -------------------------
# Insert team
# -------------------------
def add_team(tournament_id, name):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Teams (tournament_id, name) VALUES (%s, %s)",
            (tournament_id, name)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# -------------------------
# Insert match
# -------------------------
def add_match(tournament_id, team1_id, team2_id, match_date):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO Matches (tournament_id, team1_id, team2_id, match_date) VALUES (%s, %s, %s, %s)",
            (tournament_id, team1_id, team2_id, match_date)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

# -------------------------
# Update match result + points table
# -------------------------
def update_match_result(match_id, team1_score, team2_score):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute(
            "SELECT team1_id, team2_id, tournament_id FROM Matches WHERE match_id=%s",
            (match_id,)
        )
        match = cursor.fetchone()
        team1_id = match['team1_id']
        team2_id = match['team2_id']
        tournament_id = match['tournament_id']

        if team1_score > team2_score:
            winner_id = team1_id
            loser_id = team2_id
            winner_points, loser_points = 2, 0
        elif team2_score > team1_score:
            winner_id = team2_id
            loser_id = team1_id
            winner_points, loser_points = 2, 0
        else:
            winner_id = None
            winner_points = loser_points = 1

        cursor.execute(
            "UPDATE Matches SET team1_score=%s, team2_score=%s, winner_id=%s WHERE match_id=%s",
            (team1_score, team2_score, winner_id, match_id)
        )

        for team_id in [team1_id, team2_id]:
            cursor.execute(
                "SELECT * FROM Points_Table WHERE team_id=%s AND tournament_id=%s",
                (team_id, tournament_id)
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                    UPDATE Points_Table
                    SET matches_played = matches_played + 1,
                        wins = wins + %s,
                        losses = losses + %s,
                        draws = draws + %s,
                        points = points + %s
                    WHERE team_id=%s AND tournament_id=%s
                """, (
                    1 if team_id == winner_id else 0,
                    1 if winner_id and team_id != winner_id else 0,
                    1 if winner_id is None else 0,
                    winner_points if team_id == winner_id else (loser_points if winner_id else 1),
                    team_id,
                    tournament_id
                ))
            else:
                cursor.execute("""
                    INSERT INTO Points_Table (tournament_id, team_id, matches_played, wins, losses, draws, points)
                    VALUES (%s, %s, 1, %s, %s, %s, %s)
                """, (
                    tournament_id,
                    team_id,
                    1 if team_id == winner_id else 0,
                    1 if winner_id and team_id != winner_id else 0,
                    1 if winner_id is None else 0,
                    winner_points if team_id == winner_id else (loser_points if winner_id else 1)
                ))

        conn.commit()
    finally:
        cursor.close()
        conn.close()

# -------------------------
# Main UI
# -------------------------

# Header
st.markdown('<h1 class="main-header">🏆 Sports Event Manager</h1>', unsafe_allow_html=True)

# Sidebar with enhanced styling
with st.sidebar:
    st.markdown("## 📋 Navigation")
    
    menu = st.radio(
        "",
        ["🏠 Dashboard", "🏆 Add Tournament", "🗑️ Delete Tournament", "👥 Add Teams", 
         "📅 Schedule Match", "📊 Update Results", "📁 Upload CSV", "🏅 Standings"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### 📈 Quick Stats")
    
    # Quick stats in sidebar
    tournaments = get_tournaments()
    total_tournaments = len(tournaments)
    
    st.metric("Total Tournaments", total_tournaments, delta=None)
    
    if tournaments:
        latest_tournament = tournaments[-1]['name']
        st.info(f"🆕 Latest: {latest_tournament}")

# Dashboard
if menu == "🏠 Dashboard":
    st.markdown('<h2 class="sub-header">📊 Dashboard Overview</h2>', unsafe_allow_html=True)
    
    if not tournaments:
        st.markdown("""
        <div class="info-card">
            <h3>👋 Welcome to Sports Event Manager!</h3>
            <p>Get started by creating your first tournament. Use the sidebar to navigate through different features.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display tournament cards
        cols = st.columns(min(3, len(tournaments)))
        for idx, tournament in enumerate(tournaments):
            with cols[idx % 3]:
                team_count, match_count, completed = get_tournament_stats(tournament['tournament_id'])
                
                st.markdown(f"""
                <div class="tournament-card">
                    <h4>🏆 {tournament['name']}</h4>
                    <p><strong>📅 Start:</strong> {tournament['start_date']}</p>
                    <p><strong>📅 End:</strong> {tournament['end_date']}</p>
                    <p><strong>👥 Teams:</strong> {team_count}</p>
                    <p><strong>⚽ Matches:</strong> {completed}/{match_count} completed</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Recent matches
        st.markdown('<h3 class="sub-header">🔥 Recent Matches</h3>', unsafe_allow_html=True)
        matches = get_matches()
        if matches:
            recent_matches = matches[:5]  # Show last 5 matches
            
            for match in recent_matches:
                col1, col2, col3 = st.columns([2, 1, 2])
                
                with col1:
                    st.write(f"**{match['team1_name']}**")
                    if match['team1_score'] is not None:
                        st.write(f"Score: {match['team1_score']}")
                
                with col2:
                    st.write("⚡ VS")
                    if match['match_date']:
                        st.write(f"📅 {match['match_date']}")
                
                with col3:
                    st.write(f"**{match['team2_name']}**")
                    if match['team2_score'] is not None:
                        st.write(f"Score: {match['team2_score']}")
                
                st.markdown("---")

# Add Tournament
elif menu == "🏆 Add Tournament":
    st.markdown('<h2 class="sub-header">🏆 Create New Tournament</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Tournament Details")
        name = st.text_input("🏆 Tournament Name", placeholder="Enter tournament name...")
        start_date = st.date_input("📅 Start Date", value=datetime.now().date())
    
    with col2:
        st.markdown("### Schedule")
        end_date = st.date_input("📅 End Date", value=datetime.now().date())
        
        if name and start_date and end_date:
            st.success("✅ Ready to create!")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    with col_btn2:
        if st.button("🚀 Create Tournament", use_container_width=True):
            if name and start_date and end_date:
                if end_date >= start_date:
                    add_tournament(name, start_date, end_date)
                    st.markdown("""
                    <div class="success-message">
                        🎉 Tournament Created Successfully!
                    </div>
                    """, unsafe_allow_html=True)
                    st.balloons()
                else:
                    st.error("❌ End date must be after start date!")
            else:
                st.error("❌ Please fill all fields!")

# Delete Tournament
elif menu == "🗑️ Delete Tournament":
    st.markdown('<h2 class="sub-header">🗑️ Delete Tournament</h2>', unsafe_allow_html=True)
    
    if not tournaments:
        st.info("📭 No tournaments available to delete.")
    else:
        st.warning("⚠️ **Warning:** This will permanently delete the tournament and all associated data!")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            tournament_names = {t['name']: t['tournament_id'] for t in tournaments}
            selected_tournament_name = st.selectbox(
                "🏆 Select Tournament to Delete", 
                list(tournament_names.keys()),
                help="Choose the tournament you want to delete"
            )
            
            if selected_tournament_name:
                selected_tournament = next(t for t in tournaments if t['name'] == selected_tournament_name)
                st.info(f"""
                **Tournament:** {selected_tournament['name']}  
                **Period:** {selected_tournament['start_date']} to {selected_tournament['end_date']}
                """)
        
        with col2:
            st.markdown("### Confirm Deletion")
            confirm = st.checkbox("I understand this action cannot be undone")
            
            if st.button("🗑️ Delete Tournament", type="secondary", use_container_width=True):
                if confirm:
                    delete_tournament(tournament_names[selected_tournament_name])
                    st.success(f"✅ Tournament '{selected_tournament_name}' deleted successfully!")
                    st.rerun()
                else:
                    st.error("❌ Please confirm deletion by checking the checkbox!")

# Add Teams
elif menu == "👥 Add Teams":
    st.markdown('<h2 class="sub-header">👥 Add Teams to Tournament</h2>', unsafe_allow_html=True)
    
    if not tournaments:
        st.info("📭 No tournaments available. Create a tournament first!")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            tournament_names = {t['name']: t['tournament_id'] for t in tournaments}
            selected_tournament_name = st.selectbox(
                "🏆 Select Tournament", 
                list(tournament_names.keys())
            )
            
            team_name = st.text_input("👥 Team Name", placeholder="Enter team name...")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn2:
                if st.button("➕ Add Team", use_container_width=True):
                    if team_name:
                        add_team(tournament_names[selected_tournament_name], team_name)
                        st.success(f"✅ Team '{team_name}' added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Please enter a team name!")
        
        with col2:
            if selected_tournament_name:
                st.markdown("### 📋 Current Teams")
                teams = get_teams(tournament_names[selected_tournament_name])
                if teams:
                    for idx, team in enumerate(teams, 1):
                        st.markdown(f"**{idx}.** {team['name']}")
                else:
                    st.info("No teams added yet.")

# Schedule Match
elif menu == "📅 Schedule Match":
    st.markdown('<h2 class="sub-header">📅 Schedule New Match</h2>', unsafe_allow_html=True)
    
    if not tournaments:
        st.info("📭 No tournaments available. Create a tournament first!")
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            tournament_names = {t['name']: t['tournament_id'] for t in tournaments}
            selected_tournament_name = st.selectbox(
                "🏆 Select Tournament", 
                list(tournament_names.keys())
            )
            
            teams = get_teams(tournament_names[selected_tournament_name])
            if len(teams) < 2:
                st.warning("⚠️ At least 2 teams are required to schedule a match!")
            else:
                team_names = {t['name']: t['team_id'] for t in teams}
                
                team1_name = st.selectbox("🔴 Select Team 1", list(team_names.keys()))
                team2_name = st.selectbox("🔵 Select Team 2", list(team_names.keys()))
        
        with col2:
            match_date = st.date_input("📅 Match Date", value=datetime.now().date())
            
            st.markdown("### 🆚 Match Preview")
            if len(teams) >= 2 and team1_name != team2_name:
                st.markdown(f"""
                **🔴 {team1_name}**  
                        VS  
                **🔵 {team2_name}**
                
                📅 **Date:** {match_date}
                """)
            elif team1_name == team2_name:
                st.error("❌ Teams cannot play against themselves!")
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
        with col_btn2:
            if st.button("📅 Schedule Match", use_container_width=True):
                if len(teams) >= 2 and team1_name != team2_name:
                    add_match(
                        tournament_names[selected_tournament_name],
                        team_names[team1_name],
                        team_names[team2_name],
                        match_date
                    )
                    st.success("✅ Match scheduled successfully!")
                    st.balloons()

# Update Results
elif menu == "📊 Update Results":
    st.markdown('<h2 class="sub-header">📊 Update Match Results</h2>', unsafe_allow_html=True)
    
    matches = get_matches()
    if not matches:
        st.info("📭 No matches scheduled yet.")
    else:
        # Filter pending matches
        pending_matches = [m for m in matches if m['team1_score'] is None]
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if not pending_matches:
                st.info("✅ All matches have been completed!")
            else:
                match_options = {f"🆚 {m['team1_name']} vs {m['team2_name']} ({m['tournament_name']})": m['match_id'] for m in pending_matches}
                selected_match = st.selectbox("⚽ Select Match", list(match_options.keys()))
                
                if selected_match:
                    selected_match_data = next(m for m in pending_matches if m['match_id'] == match_options[selected_match])
                    
                    st.markdown(f"### 🏟️ Match Details")
                    st.info(f"""
                    **🔴 Team 1:** {selected_match_data['team1_name']}  
                    **🔵 Team 2:** {selected_match_data['team2_name']}  
                    **📅 Date:** {selected_match_data['match_date']}  
                    **🏆 Tournament:** {selected_match_data['tournament_name']}
                    """)
        
        with col2:
            if pending_matches and selected_match:
                st.markdown("### 📊 Enter Scores")
                
                team1_score = st.number_input(
                    f"🔴 {selected_match_data['team1_name']} Score", 
                    min_value=0, 
                    step=1,
                    help="Enter the final score"
                )
                
                team2_score = st.number_input(
                    f"🔵 {selected_match_data['team2_name']} Score", 
                    min_value=0, 
                    step=1,
                    help="Enter the final score"
                )
                
                # Show match result preview
                if team1_score > team2_score:
                    st.success(f"🏆 Winner: {selected_match_data['team1_name']}")
                elif team2_score > team1_score:
                    st.success(f"🏆 Winner: {selected_match_data['team2_name']}")
                else:
                    st.info("🤝 Match Result: Draw")
                
                if st.button("✅ Update Result", use_container_width=True):
                    update_match_result(match_options[selected_match], team1_score, team2_score)
                    st.success("🎉 Result updated and points table refreshed!")
                    st.rerun()

# Upload CSV
elif menu == "📁 Upload CSV":
    st.markdown('<h2 class="sub-header">📁 Upload CSV Data</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Upload CSV (Teams or Matches)", 
            type=["csv"],
            help="Upload a CSV file containing teams or match data"
        )
        
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
            st.markdown("### 📊 Preview Data")
            st.dataframe(df, use_container_width=True)
    
    with col2:
        st.markdown("### 📋 CSV Format Guide")
        st.info("""
        **For Teams CSV:**
        - tournament_name
        - team_name
        
        **For Matches CSV:**
        - tournament_name
        - team1_name  
        - team2_name
        - match_date
        """)
        
        if uploaded_file is not None:
            st.warning("⚠️ Implement CSV processing logic based on your requirements!")

# Standings
elif menu == "🏅 Standings":
    st.markdown('<h2 class="sub-header">🏅 Tournament Standings</h2>', unsafe_allow_html=True)
    
    if not tournaments:
        st.info("📭 No tournaments available.")
    else:
        tournament_names = {t['name']: t['tournament_id'] for t in tournaments}
        selected_tournament_name = st.selectbox(
            "🏆 Select Tournament", 
            list(tournament_names.keys())
        )
        
        conn = get_connection()
        try:
            df = pd.read_sql(
                """SELECT t.name AS team_name, pt.matches_played, pt.wins, pt.losses, 
                          pt.draws, pt.points 
                   FROM Points_Table pt 
                   JOIN Teams t ON pt.team_id = t.team_id 
                   WHERE pt.tournament_id = %s 
                   ORDER BY pt.points DESC, pt.wins DESC""",
                conn,
                params=(tournament_names[selected_tournament_name],)
            )
        finally:
            conn.close()
        
        if df.empty:
            st.info("📊 No standings data available. Complete some matches first!")
        else:
            # Add position column
            df.insert(0, 'Position', range(1, len(df) + 1))
            
            # Style the dataframe
            st.markdown("### 📊 Current Standings")
            
            # Create metrics for top 3
            if len(df) >= 3:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>🥇 1st Place</h3>
                        <h4>{df.iloc[0]['team_name']}</h4>
                        <p>{df.iloc[0]['points']} Points</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>🥈 2nd Place</h3>
                        <h4>{df.iloc[1]['team_name']}</h4>
                        <p>{df.iloc[1]['points']} Points</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <h3>🥉 3rd Place</h3>
                        <h4>{df.iloc[2]['team_name']}</h4>
                        <p>{df.iloc[2]['points']} Points</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display full standings table
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Position": st.column_config.NumberColumn("🏆 Pos", width="small"),
                    "team_name": st.column_config.TextColumn("👥 Team Name", width="medium"),
                    "matches_played": st.column_config.NumberColumn("⚽ MP", width="small"),
                    "wins": st.column_config.NumberColumn("✅ W", width="small"),
                    "losses": st.column_config.NumberColumn("❌ L", width="small"),
                    "draws": st.column_config.NumberColumn("🤝 D", width="small"),
                    "points": st.column_config.NumberColumn("📊 Pts", width="small"),
                }
            )
            
            # Points chart
            if len(df) > 1:
                st.markdown("### 📈 Points Distribution")
                fig = px.bar(
                    df, 
                    x='team_name', 
                    y='points',
                    color='points',
                    color_continuous_scale='viridis',
                    title="Team Points Comparison"
                )
                fig.update_layout(
                    xaxis_title="Teams",
                    yaxis_title="Points",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    '<p style="text-align: center; color: #888;">🏆 Sports Event Manager - Manage your tournaments with style! 🏆</p>', 
    unsafe_allow_html=True
)