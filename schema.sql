-- Function to update interviews' text-search columns for questions and answers
CREATE OR REPLACE FUNCTION interviews_textarrays_update_trigger()
    RETURNS trigger AS $$
begin
    new.tsquestions := to_tsvector('pg_catalog.portuguese',
                                    array_to_string(new.questions, chr(10)));
    new.tsanswers := to_tsvector('pg_catalog.portuguese',
                                    array_to_string(new.answers, chr(10)));
    return new;
end
$$ LANGUAGE plpgsql;

-- Table: public.interviews
-- TODO: Create foreign key referencing other tables
-- DROP TABLE public.interviews;

CREATE TABLE public.interviews
(
    id integer NOT NULL,
    text text COLLATE pg_catalog."default" NOT NULL,
    questions text[] COLLATE pg_catalog."default" NOT NULL,
    answers text[] COLLATE pg_catalog."default" NOT NULL,
    tstext tsvector NOT NULL,
    tsquestions tsvector NOT NULL,
    tsanswers tsvector NOT NULL,
    CONSTRAINT interviews_pkey PRIMARY KEY (id),
    CONSTRAINT interviews_id_check CHECK (id > 0)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE public.interviews
    OWNER to andre;

-- Index: interviews_idx_tsquestions

-- DROP INDEX public.interviews_idx_tsquestions;

CREATE INDEX interviews_idx_tsquestions
    ON public.interviews USING gin
    (tsquestions)
    TABLESPACE pg_default;

-- Index: interviews_idx_tsanswers

-- DROP INDEX public.interviews_idx_tsanswers;

CREATE INDEX interviews_idx_tsanswers
    ON public.interviews USING gin
    (tsanswers)
    TABLESPACE pg_default;

-- Index: interviews_idx_tstext

-- DROP INDEX public.interviews_idx_tstext;

CREATE INDEX interviews_idx_tstext
    ON public.interviews USING gin
    (tstext)
    TABLESPACE pg_default;

-- Trigger: interviews_trigg_textarrays

-- DROP TRIGGER interviews_trigg_textarrays ON public.interviews;

CREATE TRIGGER interviews_trigg_textarrays
    BEFORE INSERT OR UPDATE 
    ON public.interviews
    FOR EACH ROW
    EXECUTE PROCEDURE public.interviews_textarrays_update_trigger();

-- Trigger: interviews_trigg_tstext

-- DROP TRIGGER interviews_trigg_tstext ON public.interviews;

CREATE TRIGGER interviews_trigg_tstext
    BEFORE INSERT OR UPDATE 
    ON public.interviews
    FOR EACH ROW
    EXECUTE PROCEDURE
        tsvector_update_trigger('tstext', 'pg_catalog.portuguese', 'text');
