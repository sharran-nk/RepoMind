import faiss
import numpy as np


class VectorStore:


    def __init__(self):

        self.index = None
        self.chunks = []
        self.id_to_chunk = {}



    @staticmethod
    def get_vector_id(file_path: str, chunk_index: int) -> int:
        import hashlib
        normalized_path = file_path.replace("\\", "/")
        key = f"{normalized_path}:{chunk_index}"
        return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)



    @classmethod
    def from_index(cls, index, chunks):

        """
        Wrap an already-built FAISS index (e.g. loaded from the
        on-disk cache) without re-embedding or rebuilding anything.
        Upgrades legacy raw IndexFlatL2 indices to IndexIDMap on the fly.
        """

        store = cls()

        # Check if loaded index is a legacy index (not IndexIDMap)
        if index is not None and not isinstance(index, faiss.IndexIDMap):
            print("Converting legacy FAISS index to IndexIDMap...")
            dimension = index.d
            ntotal = index.ntotal
            
            # Reconstruct all vectors from the legacy IndexFlatL2
            vectors = np.zeros((ntotal, dimension), dtype=np.float32)
            for i in range(ntotal):
                vectors[i] = index.reconstruct(i)
                
            # Build a new IndexIDMap
            flat_index = faiss.IndexFlatL2(dimension)
            id_map_index = faiss.IndexIDMap(flat_index)
            
            # Assign deterministic IDs
            ids = []
            for idx, chunk in enumerate(chunks):
                chunk_idx = chunk.get("chunk_index", idx)
                v_id = cls.get_vector_id(chunk["file"], chunk_idx)
                ids.append(v_id)
                
            if len(ids) == ntotal:
                ids_arr = np.array(ids, dtype=np.int64)
                id_map_index.add_with_ids(vectors, ids_arr)
                index = id_map_index
            else:
                print("Warning: chunk count mismatch during legacy index conversion. Rebuilding flat index.")
                index = id_map_index

        store.index = index
        store.chunks = chunks
        
        # Build the id_to_chunk map using deterministic vector IDs
        for idx, chunk in enumerate(chunks):
            chunk_idx = chunk.get("chunk_index", idx)
            v_id = cls.get_vector_id(chunk["file"], chunk_idx)
            store.id_to_chunk[v_id] = chunk

        return store



    def build_index(self, embeddings, chunks):


        vectors = np.array(
            embeddings
        ).astype(
            "float32"
        )


        dimension = vectors.shape[1]


        flat_index = faiss.IndexFlatL2(
            dimension
        )
        self.index = faiss.IndexIDMap(flat_index)

        # Generate deterministic vector IDs for all chunks
        ids = []
        for idx, chunk in enumerate(chunks):
            chunk_idx = chunk.get("chunk_index", idx)
            v_id = self.get_vector_id(chunk["file"], chunk_idx)
            ids.append(v_id)
            self.id_to_chunk[v_id] = chunk

        ids_arr = np.array(ids, dtype=np.int64)
        self.index.add_with_ids(
            vectors,
            ids_arr
        )


        self.chunks = chunks


        print(
            "Vector database created with IndexIDMap"
        )



    def search(self, query_embedding, top_k=5):


        if self.index is None or not self.chunks:

            return []


        top_k = min(
            top_k,
            len(self.chunks)
        )


        query_vector = np.array(
            [query_embedding]
        ).astype(
            "float32"
        )


        distances, indexes = (
            self.index.search(
                query_vector,
                top_k
            )
        )


        results=[]


        for idx in indexes[0]:

            if idx == -1:

                continue

            chunk = self.id_to_chunk.get(idx)
            if chunk:
                results.append(chunk)


        return results



    def remove_vectors(self, vector_ids):
        """
        Remove vectors by their IDs from the FAISS IndexIDMap and clean up internal list/map.
        """
        if self.index is not None and len(vector_ids) > 0:
            ids_arr = np.array(vector_ids, dtype=np.int64)
            self.index.remove_ids(ids_arr)
            for v_id in vector_ids:
                if v_id in self.id_to_chunk:
                    chunk = self.id_to_chunk.pop(v_id)
                    if chunk in self.chunks:
                        self.chunks.remove(chunk)



    def add_vectors(self, embeddings, chunks_to_add):
        """
        Add new vectors with deterministic IDs to the FAISS IndexIDMap and update internal list/map.
        """
        if not embeddings or not chunks_to_add:
            return

        vectors = np.array(embeddings).astype("float32")
        
        if self.index is None:
            dimension = vectors.shape[1]
            flat_index = faiss.IndexFlatL2(dimension)
            self.index = faiss.IndexIDMap(flat_index)

        ids = []
        for chunk in chunks_to_add:
            v_id = self.get_vector_id(chunk["file"], chunk["chunk_index"])
            ids.append(v_id)
            self.id_to_chunk[v_id] = chunk
            self.chunks.append(chunk)

        ids_arr = np.array(ids, dtype=np.int64)
        self.index.add_with_ids(vectors, ids_arr)
