import pandas as pd
from PIL import Image
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import json
from utils import vector_to_raster, raw_to_lines, lines_to_strokes, to_big_strokes, clean_strokes, to_normal_strokes, strokes_to_lines, stroke_to_quickdraw, image_to_dict
import numpy as np
from tensorflow import keras
import matplotlib.pyplot as plt
from rdp import rdp
import random
import io
import requests
from json import JSONEncoder

if "none" not in st.session_state:
    st.session_state["none"]=True

if "mobile" not in st.session_state:
    st.session_state['mobile']=False

@st.experimental_memo
def print_title(a=0):
    class_name_list = ['angel',
                        'ant',
                        'axe',
                        'basketball',
                        'bathtub',
                        'bear',
                        'bed',
                        'brain',
                        'bridge',
                        'cactus',
                        'calculator',
                        'camel',
                        'camera',
                        'car',
                        'carrot',
                        'castle',
                        'cat',
                        'church',
                        'circle',
                        'cloud',
                        'coffee cup',
                        'couch',
                        'cow',
                        'crayon',
                        'crocodile',
                        'crown',
                        'diamond',
                        'dog',
                        'dolphin',
                        'door',
                        'elephant',
                        'eye',
                        'fish',
                        'flamingo',
                        'flower',
                        'fork',
                        'frog',
                        'giraffe',
                        'guitar',
                        'hamburger',
                        'hammer',
                        'hand',
                        'harp',
                        'hat',
                        'hedgehog',
                        'helicopter',
                        'horse',
                        'leaf',
                        'line',
                        'lion',
                        'lobster',
                        'mailbox',
                        'matches',
                        'motorbike',
                        'mountain',
                        'mouse',
                        'mouth',
                        'mushroom',
                        'pants',
                        'paper clip',
                        'parachute',
                        'pear',
                        'peas',
                        'pig',
                        'pineapple',
                        'pizza',
                        'rabbit',
                        'rain',
                        'rainbow',
                        'river',
                        'roller coaster',
                        'scorpion',
                        'shoe',
                        'skull',
                        'snail',
                        'snake',
                        'snowflake',
                        'spider',
                        'spoon',
                        'square',
                        'stairs',
                        'star',
                        'stethoscope',
                        'strawberry',
                        'sun',
                        'sword',
                        't-shirt',
                        'table',
                        'telephone',
                        'television',
                        'tiger',
                        'toilet',
                        'tooth',
                        'tornado',
                        'traffic light',
                        'umbrella',
                        'violin',
                        'whale',
                        'wheel',
                        'windmill']

    draw_to = class_name_list[np.random.randint(50)]
    return draw_to

# Create a canvas component
st.set_page_config(page_title="Deep Draw", page_icon="🎨", layout="wide")


#st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
#device = st.radio('', ('Computer', 'Mobile'))

if st.session_state['mobile']:
    st.session_state['mobile']=True
    gap='0px'
    ici='3'
else:
    st.session_state['mobile']=False
    gap='4px'
    ici='6'

draw_f = print_title()

st.markdown(f"<h1 style='text-align: left; color: grey;'>Draw me a {draw_f.title()}</h1>", unsafe_allow_html=True)

col1, col2= st.columns([60,40])

with col1:
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",  # Fixed fill color with some opacity
        stroke_width=1,
        stroke_color="#000",
        background_color="#eee",
        background_image=None,
        update_streamlit=True,
        height=340 if st.session_state['mobile'] else 510,
        width=340 if st.session_state['mobile'] else 800,
        drawing_mode="freedraw",
        point_display_radius=0,
        key=f'{"canva1" if st.session_state["none"] else "canva2"}{"1" if st.session_state["mobile"] else "2"}',
        initial_drawing=None
    )

#st.write(f'len canvas : {canvas_result.json_data["objects"][-1] if len(canvas_result.json_data["objects"])>0 else 0}')
try:
    objects = pd.json_normalize(canvas_result.json_data["objects"])

    path = []
    for i in range(len(objects["path"])):
        path.append(list(objects["path"][i][1:-1]))

    quickdraw_format = []
    for i in range(len(path)):
        x = [point[1] for point in path[i]]
        y = [point[2] for point in path[i]]
        quickdraw_format.append([x, y])

    ndjson_format = {}
    ndjson_format["drawing"] = quickdraw_format
    ndjson_format["word"] = "Live drawing"
    ndjson_format["key_id"] = "1"
    ndjson_format["countrycode"] = "FR"

    #Step 1
    raw_lines = raw_to_lines(quickdraw_format)
    raw_strokes_3 = lines_to_strokes(raw_lines, delta=False)

    # Step 2
    raw_strokes_3 = to_big_strokes(raw_strokes_3, max_len=5000)
    raw_strokes_3 = np.array(clean_strokes(raw_strokes_3, factor=1))
    raw_strokes_3 = to_normal_strokes(raw_strokes_3)

    # Steps 3&4
    lower = np.min(raw_strokes_3[:, 0:2], axis=0)
    upper = np.max(raw_strokes_3[:, 0:2], axis=0)
    scale = upper - lower
    scale[scale == 0] = 1
    raw_strokes_3[:, 0:2] = (raw_strokes_3[:, 0:2] - lower)*255 / scale

    # Step 5
    raw_strokes_3[1:, 0:2] -= raw_strokes_3[:-1, 0:2]

    # Step 6
    lines = strokes_to_lines(raw_strokes_3)
    simp_lines = []
    N = len(lines)
    for i in range(N):
        line = rdp(lines[i], epsilon=2)
        simp_lines.append(line)

    # Step 7
    simp_strokes_3 = lines_to_strokes(simp_lines, delta=True)
    simp_strokes_3 = np.round(simp_strokes_3).astype(float)
    strokes = stroke_to_quickdraw(simp_strokes_3, max_dim_size=255)

    #we have now 'quickdraw_format' as the path and 'bitmap_format' for the bitmap
    bitmap_format = np.array(vector_to_raster([strokes], side=28)).reshape(1, 28, 28, 1)
    json_to_api = image_to_dict(bitmap_format)
    json_to_api_2 = json.dumps(json_to_api)
    url = 'https://deepdrawimagernncnn-do5ciztupa-ew.a.run.app/predict/'
    #url = 'https://deepdrawimage2-do5ciztupa-ew.a.run.app/predict/'
    #url = 'http://127.0.0.1:8000/predict'
    with requests.Session() as s:
        response = s.post(url, json_to_api_2)
        dico = response.json()['class']
except:
    pass



with col2:
    plt.rcdefaults()
    fig, ax = plt.subplots()
    # Example data
    if 'dico' in locals():
        categories = [key.title() for key in dico.keys()]
        values= dico.values()
        ax.barh([0,1,2,3,4], values, align='center', color=plt.cm.Greens_r([0,10,50,150,200]))
        ax.set_yticks([0,1,2,3,4], labels=categories, fontsize=20)
        ax.get_yticklabels()[0].set_color("green")
        ax.invert_yaxis()  # labels read top-to-bottom
        ax.set_title('Probabilities', fontsize=20)
        for i, v in zip([0,1,2,3,4], dico.values()):
            ax.text(v +0.01, i+0.1, f"{int(v*100)} %", color='black')
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')
        ax.spines['bottom'].set_color('none')
        for xlabel_i in ax.get_xticklabels():
            xlabel_i.set_fontsize(0.0)
            xlabel_i.set_visible(False)
        for tick in ax.get_xticklines():
            tick.set_visible(False)
        st.pyplot(fig)
        del(dico)

    @st.experimental_memo()
    def change_id():
        st.session_state["none"]=not st.session_state["none"]
        st.experimental_memo.clear()
        print_title(5)

    if st.button("Next ?", on_click=change_id):
        pass

st.markdown(
    '''<style>   div[data-testid=“stHorizontalBlock”]  {gap:'''+
    gap+
    ''';    \}</style>''',
    unsafe_allow_html=True,
)

st.markdown(
   '''<style>  div.css-18e3th9
     {
    padding: 1rem '''+ici+'''em 10rem; '''
    ''';    }</style>''',
    unsafe_allow_html=True,
)

st.markdown("""
<style>
div.stButton > button:first-child {
    background-color: #EBC034;
    color: Black;
    font-weight : Bold;
    border: 2px solid #EBC034;

}
</style>""", unsafe_allow_html=True)
