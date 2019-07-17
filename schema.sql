-- Function to update interviews' text-search columns for questions and answers
CREATE OR REPLACE FUNCTION interviews_textarrays_update_trigger()
    RETURNS trigger AS $$
begin
    new.tsperguntas := to_tsvector('pg_catalog.portuguese',
                                    array_to_string(new.perguntas, chr(10)));
    new.tsrespostas := to_tsvector('pg_catalog.portuguese',
                                    array_to_string(new.respostas, chr(10)));
    return new;
end
$$ LANGUAGE plpgsql;

-- Table: public.interviews
-- TODO: Create foreign key referencing other tables
-- DROP TABLE public.interviews;

CREATE TABLE public.interviews
(
    id integer NOT NULL,
    texto text COLLATE pg_catalog."default" NOT NULL,
    perguntas text[] COLLATE pg_catalog."default" NOT NULL,
    respostas text[] COLLATE pg_catalog."default" NOT NULL,
    tstexto tsvector NOT NULL,
    tsperguntas tsvector NOT NULL,
    tsrespostas tsvector NOT NULL,
    CONSTRAINT interviews_pkey PRIMARY KEY (id),
    CONSTRAINT interviews_id_check CHECK (id > 0)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.interviews
    OWNER to andre;

-- Index: interviews_idx_tsperguntas

-- DROP INDEX public.interviews_idx_tsperguntas;

CREATE INDEX interviews_idx_tsperguntas
    ON public.interviews USING gin
    (tsperguntas)
    TABLESPACE pg_default;

-- Index: interviews_idx_tsrespostas

-- DROP INDEX public.interviews_idx_tsrespostas;

CREATE INDEX interviews_idx_tsrespostas
    ON public.interviews USING gin
    (tsrespostas)
    TABLESPACE pg_default;

-- Index: interviews_idx_tstexto

-- DROP INDEX public.interviews_idx_tstexto;

CREATE INDEX interviews_idx_tstexto
    ON public.interviews USING gin
    (tstexto)
    TABLESPACE pg_default;

-- Trigger: interviews_trigg_textarrays

-- DROP TRIGGER interviews_trigg_textarrays ON public.interviews;

CREATE TRIGGER interviews_trigg_textarrays
    BEFORE INSERT OR UPDATE 
    ON public.interviews
    FOR EACH ROW
    EXECUTE PROCEDURE public.interviews_textarrays_update_trigger();

-- Trigger: interviews_trigg_tstexto

-- DROP TRIGGER interviews_trigg_tstexto ON public.interviews;

CREATE TRIGGER interviews_trigg_tstexto
    BEFORE INSERT OR UPDATE 
    ON public.interviews
    FOR EACH ROW
    EXECUTE PROCEDURE
        tsvector_update_trigger('tstexto', 'pg_catalog.portuguese', 'texto');
