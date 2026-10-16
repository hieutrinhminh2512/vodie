"""Audio Engine and Horror FX Module."""
from .spatial_panning import SpatialAudioEngine
from .jumpscare import JumpScareController
from .dynamic_pacing import DynamicPacingController
from .voice_effects import VoiceEffectsProcessor
from .mixer import HorrorAudioMixer
from .breath_synthesizer import BreathSynthesizer
from .vocal_mastering import VocalMasteringChain

__all__ = [
    "SpatialAudioEngine",
    "JumpScareController",
    "DynamicPacingController",
    "VoiceEffectsProcessor",
    "HorrorAudioMixer",
    "BreathSynthesizer",
    "VocalMasteringChain",
]
