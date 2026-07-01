from rank_bm25 import BM25Okapi


class HybridSearch:


    def __init__(
        self,
        vector_store,
        chunks
    ):


        self.vector_store = vector_store

        self.chunks = chunks


        tokenized_code = []


        for chunk in chunks:

            tokens = (
                chunk["code"]
                .lower()
                .split()
            )

            tokenized_code.append(
                tokens
            )



        self.bm25 = BM25Okapi(
            tokenized_code
        )



    def search(
        self,
        query,
        query_embedding,
        top_k=5
    ):


        # ----------------------
        # FAISS SEARCH
        # ----------------------

        faiss_results = (
            self.vector_store.search(
                query_embedding,
                top_k
            )
        )



        # ----------------------
        # BM25 SEARCH
        # ----------------------

        query_tokens = (
            query
            .lower()
            .split()
        )


        bm25_scores = (
            self.bm25.get_scores(
                query_tokens
            )
        )



        top_indexes = (
            bm25_scores
            .argsort()
            [-top_k:]
            [::-1]
        )


        bm25_results = []


        for i in top_indexes:


            bm25_results.append(
                self.chunks[i]
            )




        # ----------------------
        # MERGE RESULTS
        # ----------------------

        final = []


        seen = set()



        max_len = max(
            len(faiss_results),
            len(bm25_results)
        )


        for i in range(max_len):


            for results in (
                faiss_results,
                bm25_results
            ):


                if i >= len(results):

                    continue


                item = results[i]


                key = (
                    item["file"],
                    item["start_line"]
                )



                if key not in seen:


                    final.append(
                        item
                    )


                    seen.add(
                        key
                    )


                if len(final) >= top_k:

                    return final



        return final[:top_k]
