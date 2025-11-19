-- Create a function to search for franchises by cosine similarity
create or replace function match_franchises (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
returns table (
  id bigint,
  franchise_name text,
  primary_category text,
  sub_categories jsonb,
  description_text text,
  similarity float
)
language plpgsql
as $$
begin
  return query (
    select
      f.id,
      f.franchise_name,
      f.primary_category,
      f.sub_categories,
      f.description_text,
      1 - (f.franchise_embedding <=> query_embedding) as similarity
    from
      "Franchises" f
    where
      1 - (f.franchise_embedding <=> query_embedding) > match_threshold
    order by
      f.franchise_embedding <=> query_embedding
    limit
      match_count
  );
end;
$$;

