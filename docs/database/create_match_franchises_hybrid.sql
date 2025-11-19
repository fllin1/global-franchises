-- Create a function to search for franchises by cosine similarity and hard filters
create or replace function match_franchises_hybrid (
  query_embedding vector(1536),
  match_threshold float,
  match_count int,
  max_budget int default null
)
returns table (
  id bigint,
  franchise_name text,
  primary_category text,
  sub_categories jsonb,
  description_text text,
  total_investment_min_usd int,
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
      f.total_investment_min_usd,
      1 - (f.franchise_embedding <=> query_embedding) as similarity
    from
      "Franchises" f
    where
      1 - (f.franchise_embedding <=> query_embedding) > match_threshold
      and (max_budget is null or f.total_investment_min_usd <= max_budget)
    order by
      f.franchise_embedding <=> query_embedding
    limit
      match_count
  );
end;
$$;
