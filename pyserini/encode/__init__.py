#
# Pyserini: Reproducible IR research with sparse and dense representations
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# This has to be first, otherwise we'll get circular import errors
from ._base import QueryEncoder, DocumentEncoder, JsonlCollectionIterator, JsonlRepresentationWriter

# Then import these...
from ._aggretriever import AggretrieverDocumentEncoder, AggretrieverQueryEncoder
from ._ance import AnceEncoder, AnceDocumentEncoder, AnceQueryEncoder
from ._auto import AutoQueryEncoder, AutoDocumentEncoder
from ._bpr import BprQueryEncoder
from ._cached_data import CachedDataQueryEncoder
from ._clip import ClipDocumentEncoder, ClipTextEncoder, ClipImageEncoder
from ._cosdpr import CosDprEncoder, CosDprDocumentEncoder, CosDprQueryEncoder
from ._dkrr import DkrrDprQueryEncoder
from ._dpr import DprDocumentEncoder, DprQueryEncoder
from ._openai import OpenAIDocumentEncoder, OpenAIQueryEncoder, OPENAI_API_RETRY_DELAY
from ._slim import SlimQueryEncoder
from ._splade import SpladeQueryEncoder
from ._tct_colbert import TctColBertDocumentEncoder, TctColBertQueryEncoder
from ._tok_freq import TokFreqQueryEncoder
from ._unicoil import UniCoilEncoder, UniCoilDocumentEncoder, UniCoilQueryEncoder
