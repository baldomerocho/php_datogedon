"""Datogedon native TikTok favorites and evidence required for new uploads."""
from copy import deepcopy
import math

POLICY = {
    'version': 1,
    'required': True,
    'source': 'tiktok_favorites',
    'user_reported_min_duration_seconds': 180,
    'default': 'Closed Slip',
    'favorites': [
        {'title': 'Closed Slip', 'gain_db': -12, 'use': 'General; ambiental y melancólico'},
        {'title': 'Shard Pact', 'gain_db': -14, 'use': 'Electro tranquilo, lento y melancólico; remates ocasionales'},
        {'title': 'Bonefire Circle', 'gain_db': -16, 'use': 'Solo temas alegres; ritmo tipo samba'},
        {'title': 'The Turnin of Titans', 'gain_db': -16, 'use': 'Épica o suspenso cuando el tema lo justifique'},
    ],
}

def policy():
    return deepcopy(POLICY)

def verify(music):
    if not isinstance(music, dict):
        raise ValueError('TikTok background music evidence required')
    favorite = next((f for f in POLICY['favorites'] if f['title'] == music.get('favorite_title')), None)
    if not favorite:
        raise ValueError('Select a Datogedon TikTok favorite')
    for field in ('native_sound_id', 'native_title', 'version', 'selection_reason', 'volume_evidence'):
        if not isinstance(music.get(field), str) or not music[field].strip():
            raise ValueError('Missing TikTok music evidence: '+field)
    gain = music.get('gain_db')
    if isinstance(gain, bool) or not isinstance(gain, (int, float)) or not math.isfinite(gain) or gain != favorite['gain_db']:
        raise ValueError('TikTok music must use the configured favorite gain')
    if music.get('source') != POLICY['source']:
        raise ValueError('TikTok music must be selected natively from Favorites')
    for field in ('full_duration_verified', 'voice_preserved', 'mix_checked'):
        if music.get(field) is not True:
            raise ValueError('Missing TikTok music verification: '+field)
